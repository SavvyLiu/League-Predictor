"""Read-only Riot API pilot. Fetch completed matches; never train or publish."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import json
import os
from pathlib import Path
import time
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parent
ROUTES = {'na1': 'americas', 'euw1': 'europe', 'eun1': 'europe',
          'kr': 'asia', 'jp1': 'asia', 'br1': 'americas', 'tr1': 'europe',
          'la1': 'americas', 'la2': 'americas', 'oc1': 'sea',
          'ph2': 'sea', 'sg2': 'sea', 'th2': 'sea', 'tw2': 'sea', 'vn2': 'sea'}


class RiotClient:
    def __init__(self):
        key_path = Path(os.environ['LOCALAPPDATA']) / '4al3/credentials/riot-api-key.txt'
        key = os.environ.get('RIOT_API_KEY')
        if not key and key_path.exists():
            key = key_path.read_text(encoding='utf-8-sig').strip()
        if not key:
            raise RuntimeError('Riot key missing. Run save-api-key.ps1 -Provider Riot first.')
        self.session = requests.Session()
        self.session.headers['X-Riot-Token'] = key
        self.last_request = 0.0
        self.requests_made = 0
        self.response_status_counts = Counter()

    def get(self, routing, path, params=None):
        url = f'https://{routing}.api.riotgames.com{path}'
        for attempt in range(5):
            time.sleep(max(0, 1.3 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                response = self.session.get(url, params=params, timeout=(10, 30))
            except requests.RequestException:
                if attempt == 4:
                    raise RuntimeError('Riot request failed after retries; no credential was logged.') from None
                time.sleep(2 ** attempt)
                continue
            self.requests_made += 1
            self.response_status_counts[str(response.status_code)] += 1
            if response.status_code in (401, 403):
                raise RuntimeError(f'Riot returned HTTP {response.status_code}. Check the key, expiry, and access permissions.')
            if response.status_code == 429:
                seconds = max(1, float(response.headers.get('Retry-After', 30)))
                print(f'Rate limited. Respecting Retry-After: {seconds:g} seconds.', flush=True)
                while seconds > 0:
                    pause = min(30, seconds)
                    time.sleep(pause)
                    seconds -= pause
                continue
            if response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise RuntimeError(f'Riot returned HTTP {response.status_code}; request stopped.')
            return response.json()
        raise RuntimeError('Riot request did not succeed within the retry limit.')


def snapshot(match, timeline, minute=10, checkpoint_mode='strict'):
    info = match['info']
    participants = info.get('participants', [])
    if info.get('queueId') != 420 or info.get('mapId') != 11:
        return None
    if info.get('gameDuration', 0) <= minute * 60:
        return None
    if len(participants) != 10 or any(p.get('gameEndedInEarlySurrender') for p in participants):
        return None
    if timeline.get('info', {}).get('endOfGameResult') and timeline['info']['endOfGameResult'] != 'GameComplete':
        return None
    participant_team = {p['participantId']: p['teamId'] for p in participants}
    if Counter(participant_team.values()) != {100: 5, 200: 5}:
        return None
    cutoff = minute * 60_000
    frames = timeline['info']['frames']
    requested_cutoff = cutoff
    if checkpoint_mode == 'nominal':
        frame = min(frames, key=lambda f: abs(f['timestamp'] - cutoff))
        if abs(frame['timestamp'] - cutoff) > 5_000:
            return None
        cutoff = frame['timestamp']
    else:
        before = [f for f in frames if f['timestamp'] <= cutoff]
        if not before:
            return None
        frame = max(before, key=lambda f: f['timestamp'])
    if cutoff - frame['timestamp'] > 60_000:
        return None
    states = frame.get('participantFrames', {})
    if len(states) != 10:
        return None
    fields = ['gold', 'xp', 'level_sum', 'cs', 'jungle_cs', 'damage_to_champions',
              'kills', 'deaths', 'assists', 'wards_placed', 'wards_destroyed',
              'dragons', 'heralds', 'barons', 'void_grubs', 'towers', 'inhibitors']
    stats = {100: Counter({f: 0 for f in fields}), 200: Counter({f: 0 for f in fields})}
    for pid, state in states.items():
        team = participant_team[int(pid)]
        for out, source in [('gold', 'totalGold'), ('xp', 'xp'), ('level_sum', 'level'),
                            ('cs', 'minionsKilled'), ('jungle_cs', 'jungleMinionsKilled')]:
            if source not in state:
                return None
            stats[team][out] += state[source]
        stats[team]['damage_to_champions'] += state.get('damageStats', {}).get('totalDamageDoneToChampions', 0)
    event_types = Counter()
    event_count = 0
    for f in frames:
        for event in f.get('events', []):
            if event.get('timestamp', cutoff + 1) > cutoff:
                continue
            kind = event.get('type', '')
            event_types[kind] += 1
            event_count += 1
            if kind == 'CHAMPION_KILL':
                for key, field in [('killerId', 'kills'), ('victimId', 'deaths')]:
                    tid = participant_team.get(event.get(key))
                    if tid:
                        stats[tid][field] += 1
                for pid in event.get('assistingParticipantIds', []):
                    tid = participant_team.get(pid)
                    if tid:
                        stats[tid]['assists'] += 1
            elif kind in ('WARD_PLACED', 'WARD_KILL'):
                pid = event.get('creatorId' if kind == 'WARD_PLACED' else 'killerId')
                tid = participant_team.get(pid)
                if tid:
                    stats[tid]['wards_placed' if kind == 'WARD_PLACED' else 'wards_destroyed'] += 1
            elif kind == 'ELITE_MONSTER_KILL':
                tid = event.get('killerTeamId') or participant_team.get(event.get('killerId'))
                field = {'DRAGON': 'dragons', 'RIFTHERALD': 'heralds',
                         'BARON_NASHOR': 'barons', 'HORDE': 'void_grubs'}.get(event.get('monsterType'))
                if tid in stats and field:
                    stats[tid][field] += 1
            elif kind == 'BUILDING_KILL':
                owner = event.get('teamId')
                field = {'TOWER_BUILDING': 'towers', 'INHIBITOR_BUILDING': 'inhibitors'}.get(event.get('buildingType'))
                if owner in stats and field:
                    stats[200 if owner == 100 else 100][field] += 1
    teams = {t['teamId']: t for t in info['teams']}
    if set(teams) != {100, 200} or bool(teams[100].get('win')) == bool(teams[200].get('win')):
        return None
    row = {'match_id': match['metadata']['matchId'],
           'game_start_timestamp': info.get('gameStartTimestamp'),
           'game_version': info.get('gameVersion'), 'queue_id': info.get('queueId'),
           'checkpoint_mode': checkpoint_mode, 'requested_cutoff_ms': requested_cutoff,
           'cutoff_ms': cutoff, 'frame_timestamp_ms': frame['timestamp'],
           'blueWins': int(teams[100]['win'])}
    for field in fields:
        row['blue_' + field] = stats[100][field]
        row['red_' + field] = stats[200][field]
        row[field + '_diff'] = stats[100][field] - stats[200][field]
    return row, {'events_before_cutoff': event_count, 'event_types': dict(event_types),
                 'participant_frame_fields': sorted(next(iter(states.values()))),
                 'timeline_frame_interval_ms': timeline['info'].get('frameInterval')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=sorted(ROUTES), default='na1')
    parser.add_argument('--count', type=int, default=10)
    parser.add_argument('--riot-id', help='Optional seed in GameName#TagLine form')
    parser.add_argument('--checkpoint-mode', choices=['strict', 'nominal'], default='strict',
                        help='strict: only data available by 600s; nominal: coherent nearest frame within 5s, recording its actual timestamp')
    args = parser.parse_args()
    if not 1 <= args.count <= 25:
        parser.error('--count must be between 1 and 25 for this pilot')
    route = ROUTES[args.platform]
    client = RiotClient()
    private = ROOT / 'private' / 'riot' / args.platform
    private.mkdir(parents=True, exist_ok=True)
    if args.riot_id:
        name, tag = args.riot_id.rsplit('#', 1)
        account = client.get(route, f'/riot/account/v1/accounts/by-riot-id/{quote(name, safe="")}/{quote(tag, safe="")}')
        seeds = [account['puuid']] if account else []
    else:
        entries = client.get(args.platform, '/lol/league/v4/entries/RANKED_SOLO_5x5/DIAMOND/I', {'page': 1}) or []
        seeds = [e['puuid'] for e in entries if e.get('puuid')][:5]
        print(f'League endpoint responded; {len(entries)} entries, {len(seeds)} pilot seeds selected.', flush=True)
    if not seeds:
        raise RuntimeError('No usable seed PUUIDs returned. Supply --riot-id GameName#TagLine.')
    ids = []
    for puuid in seeds:
        discovered = client.get(route, f'/lol/match/v5/matches/by-puuid/{puuid}/ids',
                                {'queue': 420, 'count': min(100, args.count * 3)}) or []
        ids.extend(mid for mid in discovered if mid not in ids)
        if len(ids) >= args.count * 3:
            break
    rows, schema_examples = [], []
    skipped = 0
    for mid in ids:
        pair = []
        for suffix, path in [('match', f'/lol/match/v5/matches/{mid}'),
                             ('timeline', f'/lol/match/v5/matches/{mid}/timeline')]:
            cache = private / f'{mid}-{suffix}.json'
            if cache.exists():
                value = json.loads(cache.read_text(encoding='utf-8'))
            else:
                value = client.get(route, path)
                if value:
                    cache.write_text(json.dumps(value), encoding='utf-8')
            pair.append(value)
        extracted = snapshot(*pair, checkpoint_mode=args.checkpoint_mode) if all(pair) else None
        if not extracted:
            skipped += 1
            continue
        row, evidence = extracted
        rows.append(row)
        schema_examples.append({'match_id': mid, **evidence})
        print(f'Usable ten-minute matches: {len(rows)}/{args.count}', flush=True)
        if len(rows) == args.count:
            break
    output = ROOT / 'findings'
    output.mkdir(exist_ok=True)
    if rows:
        with (output / f'riot-{args.platform}-10min-{args.checkpoint_mode}-pilot.csv').open('w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summary = {'platform': args.platform, 'routing': route, 'usable_matches': len(rows),
               'checkpoint_mode': args.checkpoint_mode,
               'skipped_matches': skipped, 'blueWins_counts': dict(Counter(r['blueWins'] for r in rows)),
               'requests_made_this_run': client.requests_made,
               'response_status_counts': dict(client.response_status_counts),
               'collected_at_utc': datetime.now(timezone.utc).isoformat(),
               'scope': 'Small convenience sample for API/schema feasibility; not a representative training set.',
               'schema_examples': schema_examples}
    (output / f'riot-{args.platform}-{args.checkpoint_mode}-pilot-audit.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'schema_examples'}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from None
