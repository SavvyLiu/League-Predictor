"""Resumable, bounded Riot Match-v5 collection. Raw records always stay local."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parent
PLATFORMS = {"na1": ("americas", "na"), "euw1": ("europe", "euw")}


class RequestBudgetReached(Exception):
    pass


class KeyRefreshNeeded(Exception):
    pass


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def read_key():
    # Read again for each uncached request so replacing the file also refreshes a live run.
    override = os.environ.get("RIOT_API_KEY_FILE")
    local = os.environ.get("LOCALAPPDATA")
    path = Path(override) if override else (Path(local) / "4al3/credentials/riot-api-key.txt" if local else None)
    if path and path.exists():
        key = path.read_text(encoding="utf-8-sig").strip()
    else:
        key = os.environ.get("RIOT_API_KEY", "").strip()
    if not key.startswith("RGAPI-") or any(c.isspace() for c in key):
        raise KeyRefreshNeeded("No valid local key. Use save-api-key.ps1 -Provider Riot -Replace; never paste the key in logs.")
    return key


class Client:
    def __init__(self, maximum_requests):
        self.maximum_requests = maximum_requests
        self.network_requests = 0
        self.cache_hits = 0
        self.last_request = 0.0
        self.statuses = Counter()
        self.observed_limits = {}
        self.session = requests.Session()

    def get(self, routing, path, cache, params=None):
        if cache.exists():
            self.cache_hits += 1
            return json.loads(cache.read_text(encoding="utf-8"))
        for attempt in range(5):
            if self.network_requests >= self.maximum_requests:
                raise RequestBudgetReached()
            key = read_key()
            time.sleep(max(0, 1.3 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            self.network_requests += 1
            try:
                response = self.session.get(f"https://{routing}.api.riotgames.com{path}",
                    params=params, headers={"X-Riot-Token": key}, timeout=(10, 35))
            except requests.RequestException:
                if attempt == 4:
                    raise RuntimeError("Network request failed; cached progress is preserved.") from None
                time.sleep(2 ** attempt)
                continue
            finally:
                key = None
            self.statuses[str(response.status_code)] += 1
            for header in ("X-App-Rate-Limit", "X-Method-Rate-Limit"):
                if header in response.headers:
                    self.observed_limits[header] = response.headers[header]
            if response.status_code in (401, 403):
                raise KeyRefreshNeeded("Riot rejected credentials or access. Refresh the key or check endpoint access, then rerun the same command to resume.")
            if response.status_code == 404:
                return None
            if response.status_code == 429:
                delay = max(1.0, float(response.headers.get("Retry-After", 120)))
                print(f"Rate limit reached; waiting {delay:.0f}s as requested by Riot.", flush=True)
                time.sleep(delay)
                continue
            if response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            if response.status_code != 200:
                raise RuntimeError(f"Riot HTTP {response.status_code}; collection stopped with progress preserved.")
            try:
                result = response.json()
            except ValueError:
                raise RuntimeError("Riot returned invalid JSON; progress is preserved.") from None
            atomic_json(cache, result)
            return result
        raise RuntimeError("Retry limit reached; collection can be resumed.")


def make_manifest(args, folder):
    path = folder / "manifest.json"
    if path.exists():
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest["platform"] != args.platform:
            raise ValueError("Existing collection uses a different platform. Choose another --collection name.")
        return manifest
    region, realm = PLATFORMS[args.platform]
    response = requests.get(f"https://ddragon.leagueoflegends.com/realms/{realm}.json", timeout=25)
    response.raise_for_status()
    static = response.json()
    patch = ".".join(static["v"].split(".")[:2])
    now = datetime.now(timezone.utc)
    manifest = {"platform": args.platform, "routing": region, "queue": 420,
                "patch": patch, "realm_version": static["v"],
                "patch_source": "Regional Data Dragon realm at collection creation; gameVersion checked per accepted match",
                "window_start": int((now - timedelta(days=args.recent_days)).timestamp()),
                "window_end": int(now.timestamp()), "created_at_utc": now.isoformat(),
                "seed_tier": args.tier, "seed_division": args.division, "seed_count": args.seeds,
                "sampling": "Deterministic evenly spaced entries from one current league page; convenience sample, not population-random or verified historical match rank",
                "scope": "Raw match/timeline collection; no model trained and no raw responses published"}
    atomic_json(path, manifest)
    atomic_json(folder / "static/realm.json", static)
    return manifest


def eligibility(match, manifest):
    if match is None:
        return "match_not_found"
    info = match.get("info", {})
    if not match.get("metadata", {}).get("matchId", "").startswith(manifest["platform"].upper() + "_"):
        return "different_platform"
    if info.get("queueId") != 420 or info.get("mapId") != 11:
        return "different_queue_or_map"
    if ".".join(info.get("gameVersion", "").split(".")[:2]) != manifest["patch"]:
        return "different_patch"
    start = info.get("gameStartTimestamp", info.get("gameCreation", 0)) / 1000
    if not manifest["window_start"] <= start <= manifest["window_end"]:
        return "outside_sampling_window"
    if info.get("gameDuration", 0) <= 600:
        return "ended_before_ten_minutes"
    participants = info.get("participants", [])
    if len(participants) != 10 or Counter(p.get("teamId") for p in participants) != {100: 5, 200: 5}:
        return "incomplete_teams"
    teams = {t.get("teamId"): t for t in info.get("teams", [])}
    if set(teams) != {100, 200} or bool(teams[100].get("win")) == bool(teams[200].get("win")):
        return "ambiguous_outcome"
    return None


def status(folder):
    if not (folder / "manifest.json").exists():
        print("Collection has not been created yet.")
        return
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    counts = {}
    if (folder / "queue.sqlite3").exists():
        with sqlite3.connect(folder / "queue.sqlite3") as db:
            counts = dict(db.execute("SELECT state, COUNT(*) FROM matches GROUP BY state"))
    print(json.dumps({"collection": folder.name, "platform": manifest["platform"],
                      "patch": manifest["patch"], "realm_version": manifest["realm_version"],
                      "created_at_utc": manifest["created_at_utc"], "counts": counts,
                      "raw_data_published": False}, indent=2))


def collect(args, folder):
    folder.mkdir(parents=True, exist_ok=True)
    manifest = make_manifest(args, folder)
    client = Client(args.max_requests)
    db = sqlite3.connect(folder / "queue.sqlite3")
    db.execute("CREATE TABLE IF NOT EXISTS matches (match_id TEXT PRIMARY KEY, state TEXT NOT NULL DEFAULT 'pending', reason TEXT)")
    outcome = "completed"
    print(f"NA/EUW collection: {manifest['platform']}, pinned patch {manifest['patch']}; target {args.count} accepted matches.", flush=True)
    try:
        accepted = db.execute("SELECT COUNT(*) FROM matches WHERE state='accepted'").fetchone()[0]
        if accepted < args.count and not (folder / "discovery/complete.json").exists():
            entries = client.get(args.platform,
                f"/lol/league/v4/entries/RANKED_SOLO_5x5/{manifest['seed_tier']}/{manifest['seed_division']}",
                folder / "discovery/league-page-1.json", {"page": 1}) or []
            seeds = [e["puuid"] for e in entries if e.get("puuid")]
            number = min(manifest["seed_count"], len(seeds))
            chosen = [seeds[int(i * len(seeds) / number)] for i in range(number)] if number else []
            if not chosen:
                raise RuntimeError("League endpoint returned no usable seeds; no personal identifiers printed.")
            for seed in chosen:
                cache_id = hashlib.sha256(seed.encode()).hexdigest()[:24]
                ids = client.get(manifest["routing"], f"/lol/match/v5/matches/by-puuid/{quote(seed, safe='')}/ids",
                    folder / f"discovery/history-{cache_id}.json",
                    {"queue": 420, "startTime": manifest["window_start"], "endTime": manifest["window_end"], "count": 100}) or []
                db.executemany("INSERT OR IGNORE INTO matches(match_id) VALUES (?)", [(mid,) for mid in ids])
                db.commit()
            atomic_json(folder / "discovery/complete.json", {"seed_histories_completed": len(chosen)})
            print(f"Candidate queue built from {len(chosen)} seeds; player identifiers remain local.", flush=True)
        candidates = [r[0] for r in db.execute("SELECT match_id FROM matches WHERE state='pending' ORDER BY match_id DESC")]
        for mid in candidates:
            if accepted >= args.count:
                break
            match = client.get(manifest["routing"], f"/lol/match/v5/matches/{mid}", folder / f"matches/{mid}.json")
            reason = eligibility(match, manifest)
            if not reason:
                timeline = client.get(manifest["routing"], f"/lol/match/v5/matches/{mid}/timeline", folder / f"timelines/{mid}.json")
                frames = timeline.get("info", {}).get("frames", []) if timeline else []
                if not frames or not any(abs(f.get("timestamp", -999999) - 600000) <= 5000 and len(f.get("participantFrames", {})) == 10 for f in frames):
                    reason = "missing_complete_nominal_ten_minute_frame"
                elif timeline.get("metadata", {}).get("matchId") != mid:
                    reason = "timeline_id_mismatch"
            state = "excluded" if reason else "accepted"
            db.execute("UPDATE matches SET state=?,reason=? WHERE match_id=?", (state, reason, mid))
            db.commit()
            if not reason:
                accepted += 1
                print(f"Accepted complete match/timeline pairs: {accepted}/{args.count}", flush=True)
        if accepted < args.count:
            outcome = "candidate_queue_exhausted"
    except RequestBudgetReached:
        outcome = "request_budget_reached_resume_available"
    except KeyRefreshNeeded as error:
        outcome = "key_or_access_refresh_needed"
        print(str(error), flush=True)
    except KeyboardInterrupt:
        outcome = "interrupted_resume_available"
    except (RuntimeError, ValueError, requests.RequestException):
        outcome = "error_resume_available"
        raise
    finally:
        db.close()
        run_record = {"outcome": outcome, "network_requests": client.network_requests,
                    "cache_hits": client.cache_hits, "http_status_counts": dict(client.statuses),
                    "observed_rate_limits": client.observed_limits, "ended_at_utc": datetime.now(timezone.utc).isoformat()}
        run_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        atomic_json(folder / f"runs/{run_name}.json", run_record)
        atomic_json(folder / "last_run.json", run_record)
        print("Run outcome:", outcome, flush=True)
        status(folder)
    if outcome == "key_or_access_refresh_needed":
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["collect", "status"])
    parser.add_argument("--platform", choices=PLATFORMS, default="na1")
    parser.add_argument("--collection", default="na1-current")
    parser.add_argument("--count", type=int, default=10, help="Desired total accepted matches, including earlier runs")
    parser.add_argument("--max-requests", type=int, default=60, help="Network request budget for this invocation")
    parser.add_argument("--recent-days", type=int, default=7)
    parser.add_argument("--tier", choices=["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND"], default="DIAMOND")
    parser.add_argument("--division", choices=["I", "II", "III", "IV"], default="I")
    parser.add_argument("--seeds", type=int, default=10)
    args = parser.parse_args()
    if not args.collection or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.collection):
        parser.error("Use letters, digits, hyphens or underscores for the collection name.")
    if min(args.count, args.max_requests, args.recent_days, args.seeds) < 1:
        parser.error("Counts, budgets and days must be positive.")
    folder = ROOT / "private" / args.collection
    if args.command == "status":
        status(folder)
    else:
        collect(args, folder)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, requests.RequestException) as error:
        # Do not include raw request URLs, headers, player IDs or credentials in error output.
        print("Collection stopped:", str(error) if isinstance(error, (RuntimeError, ValueError)) else "Network error. Cached progress is preserved.")
        raise SystemExit(1) from None
