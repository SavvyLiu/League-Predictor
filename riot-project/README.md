# Fresh Riot data: NA1

This is the separate data-collection foundation for a richer League Predictor. The course's existing Kaggle experiments/report remain in `progress-report/`.

[Starter verification results](STARTER_RESULTS.md): ten fresh NA1 pairs on patch 16.22, cached successfully and checked without publishing raw player records.

## Key refresh

On this Windows setup, save/replace the developer key using:

```powershell
./project-research/save-api-key.ps1 -Provider Riot -Replace
```

The helper prompts with hidden input, validates the expected Riot-key format, and stores the key outside the repository at `%LOCALAPPDATA%\4al3\credentials\riot-api-key.txt`. Only the current Windows account and SYSTEM receive access. It is not stored in Git.

The collector rereads that file for each uncached request, so replacing it refreshes a running process too. Alternatively use `RIOT_API_KEY_FILE` for another external file, or `RIOT_API_KEY` when no key file exists. The file has priority over the environment value.

Riot development keys deactivate every 24 hours; see the [official portal documentation](https://developer.riotgames.com/docs/portal). If credentials/access are rejected, collection stops cleanly. Replace the key and rerun the same command to resume. Cache reads and the offline status command do not require a valid key.

## Start or resume a bounded run

From the repository root, install the separate collection dependency:

```sh
python -m pip install -r riot-project/requirements.txt
python riot-project/collect.py collect --platform na1 --collection na1-current --count 10 --max-requests 60
python riot-project/collect.py status --collection na1-current
python riot-project/verify_cache.py --collection na1-current
python -m unittest discover -s riot-project/tests -v
```

`--count` is the desired total accepted match/timeline pairs across runs, not an increment. Increasing it continues the same candidate queue. `--max-requests` is a per-run network budget. The current seed discovery uses ten evenly spaced entries from one Diamond I league page and up to 100 recent ranked-solo matches per selected seed. This is a convenience sample: current seed rank is not the rank of every player in every historical match. Ordinary completed surrender outcomes are retained when duration and checkpoint requirements are met.

If a run stops during seed discovery, cached responses and deduplicated candidates are reused on the next run. If the fixed sampling window's candidate queue is exhausted, the program reports that outcome; it does not silently widen the sampling window or mix patches.

## Patch and time window

When a collection is created, it records the regional Data Dragon realm version and pins its major/minor patch. The NA1 starter realm reported `16.22.1` on November 10, 2026, so the starter collection is pinned to `16.22`. Each accepted match's actual `gameVersion` is checked against that prefix. Data Dragon realm version is a documented collection signal, not a guarantee that all deployed game assets update synchronously.

The seven-day discovery window is fixed when the collection is created and is not moved on resume. Use a new collection name to start a different patch, time window or sampling configuration. Existing collections keep the manifest's original tier/division/seed count even if different creation options are passed on resume.

## Local storage and progress

`riot-project/private/<collection>/` contains:

- `manifest.json`: patch, platform, discovery window and sampling procedure;
- `queue.sqlite3`: deduplicated candidates and accepted/excluded/pending states;
- `discovery/`: league entries and seed match histories, including player identifiers;
- `matches/` and `timelines/`: complete cached Match-v5 responses;
- `static/realm.json`: the realm/version response observed at collection creation;
- `last_run.json`: request counts, HTTP statuses, observed limits and completion/stop reason.
- `runs/`: per-invocation summaries retained across key refreshes and resume attempts.

Both `private/` and future `data/` outputs are ignored by Git. Only code, tests and documentation are intended for the public repository. Completed JSON downloads are written atomically and reused. An interrupted match/timeline pair remains pending until it can be completed. Collection is paced at least 1.3 seconds between requests and obeys server `Retry-After` responses; avoid parallel collectors sharing the same key.

## What we are building toward

The raw responses preserve champion/team identities and full timeline frames/events, so we can later derive:

1. Per-player economy, XP, farming, damage and role-relative leads.
2. Champion matchups and composition features.
3. Item inventories and spending reconstructed from timestamped events.
4. Five-to-ten-minute trajectory features and later checkpoints where available.

**This collector does not yet implement those feature encodings or train the richer model.** It fetches and validates source data first. Final-match item slots/combat totals must never be used as ten-minute predictors. Item reconstruction must handle purchases, sales, destruction and undo explicitly. Roles inferred after the match also need an availability check before use.

The ten-minute acceptance check requires a complete nominal frame within five seconds of 600,000 ms. It does not claim the frame occurred exactly at ten minutes. Future extraction must record requested and actual timestamps and choose strict or nominal availability explicitly. Multiple checkpoints of one match must remain in the same modeling split; the recorded dates permit later chronological evaluation.

Official references: [League APIs and Data Dragon](https://developer.riotgames.com/docs/lol), [Match-v5](https://developer.riotgames.com/apis#match-v5), [keys and rate limiting](https://developer.riotgames.com/docs/portal).
