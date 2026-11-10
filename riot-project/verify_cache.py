"""Audit accepted local match/timeline pairs without API calls or exposing player IDs."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from collect import ROOT, atomic_json, eligibility


def verify(name):
    folder = ROOT / "private" / name
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    with sqlite3.connect(folder / "queue.sqlite3") as db:
        ids = [r[0] for r in db.execute("SELECT match_id FROM matches WHERE state='accepted'")]
    assert len(ids) == len(set(ids))
    labels, patches, champion_ids, event_types, cutoff_times, starts = Counter(), Counter(), set(), Counter(), [], []
    for mid in ids:
        match = json.loads((folder / f"matches/{mid}.json").read_text(encoding="utf-8"))
        timeline = json.loads((folder / f"timelines/{mid}.json").read_text(encoding="utf-8"))
        assert match["metadata"]["matchId"] == timeline["metadata"]["matchId"] == mid
        assert eligibility(match, manifest) is None
        frames = timeline["info"]["frames"]
        near = min(frames, key=lambda f: abs(f["timestamp"] - 600000))
        assert abs(near["timestamp"] - 600000) <= 5000
        assert set(near["participantFrames"]) == {str(i) for i in range(1, 11)}
        assert {p["participantId"] for p in match["info"]["participants"]} == set(range(1, 11))
        assert all("totalGold" in f and "xp" in f and "currentGold" in f for f in near["participantFrames"].values())
        labels[int(next(t["win"] for t in match["info"]["teams"] if t["teamId"] == 100))] += 1
        patches[match["info"]["gameVersion"]] += 1
        champion_ids.update(p["championId"] for p in match["info"]["participants"])
        cutoff_times.append(near["timestamp"])
        starts.append(match["info"]["gameStartTimestamp"])
        event_types.update(e["type"] for f in frames for e in f.get("events", []) if e.get("timestamp", 1e99) <= near["timestamp"])
    summary = {"platform": manifest["platform"], "patch": manifest["patch"], "accepted_pairs_verified": len(ids),
               "label_counts": dict(labels), "observed_game_versions": dict(patches),
               "distinct_champions": len(champion_ids), "event_types_through_nominal_ten_minutes": dict(event_types),
               "actual_nominal_frame_ms_range": [min(cutoff_times), max(cutoff_times)] if cutoff_times else None,
               "match_start_utc_range": [datetime.fromtimestamp(t/1000, timezone.utc).isoformat() for t in [min(starts), max(starts)]] if starts else None,
               "all_participant_frames_and_outcomes_verified": True,
               "scope": "Local source-schema feasibility audit, not model results or a representative training dataset"}
    atomic_json(folder / "cache_audit.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", default="na1-current")
    args = parser.parse_args()
    if not args.collection or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.collection):
        parser.error("Invalid collection name")
    verify(args.collection)
