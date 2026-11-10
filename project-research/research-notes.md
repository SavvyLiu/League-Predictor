# Dataset and Riot API investigation

Investigation date: October 9, 2026. This is an evidence notebook for the group's data-source work, not a proposal draft or a team contract.

## Decision

- The best ready-made structural alternative found is Nathan Smallcalder's [LoL Match Intervals: 2 Million In-Game Snapshots](https://www.kaggle.com/datasets/nathansmallcalder/league-of-legends-match-interval-snapshots-2026), Version 2. Its player-level snapshots can be joined and aggregated into one blue-versus-red record per match at ten minutes.
- It improves on the original dataset's provenance and flexibility: the [collection code](https://github.com/NathanSmallcalder/LeagueFiveMinIntervals/blob/main/DataCollector.py), platform, timestamps, patches, player-to-team mapping, and outcomes can be inspected. However, its licensing is unclear and several collection fields need validation. This is a conditional candidate, not a fully cleared replacement.
- Collecting a small, explicitly documented Riot Match-v5 dataset is the strongest way to control sampling, features, timestamps, and preprocessing. Live collection has now been verified with a ten-match feasibility pilot. Model-training permission remains a separate question.
- The original 9,879-match dataset remains the simpler fallback. Switching datasets does not itself establish Riot's permission for training.

## Evidence and reproducibility

The `sources/` directory holds the fetched Kaggle metadata/file manifests, API reference material, and collection-code snapshots. The `data/` directory holds four downloaded datasets and derived candidate CSVs. `findings/dataset-audit.json` contains independently computed counts, rather than relying on dataset titles. The audit can be rerun with `audit_datasets.py`.

Kaggle's public API supported metadata, file inventories, search, and downloads without authentication. The official installed CLI is Kaggle 2.2.4. After credentials were saved, a CLI dataset search also succeeded. No new plugin was necessary.

## Ready-made candidate audit

| Candidate | Inspection | Fit and limitations |
| --- | --- | --- |
| [Original Diamond 10-minute dataset](https://www.kaggle.com/datasets/bobbyscience/league-of-legends-diamond-ranked-games-10-min) | Full CSV: 9,879 distinct matches; 38 predictors plus ID and label; 4,930 blue wins and 4,949 losses; no missing cells. Listed CC0. | Exact intended task and vision statistics. Last updated April 2020; lacks verified collection dates, platform, patches, and preprocessing code. |
| [Smallcalder interval snapshots, Version 2](https://www.kaggle.com/datasets/nathansmallcalder/league-of-legends-match-interval-snapshots-2026) | Full files: 39,954 matches, 399,540 player records, 2,108,090 player-time rows. Exactly 39,385 matches have all ten players at the nominal ten-minute interval. | Best structural alternative; raw table size is not the number of independent matches. License listed as Other, with no explicit license identified in the description or linked repository. Preprocessing limitations below. |
| [Smallcalder post-match and timeline, Version 1](https://www.kaggle.com/datasets/nathansmallcalder/league-of-legends-ranked-post-match-and-timeline) | Full files: 77,135 matches, 112,688 player-match lookup rows, 3,195,293 timeline rows. Ten-minute rows map to 75,947 matches, with only 1-8 recorded players per match. Listed MIT. | Newer, but no match has all ten players at ten minutes. Individual-player timelines and some team metrics could support a revised task; they cannot reconstruct both complete team economies/XP from the published subset. |
| [EUW Apex 14-minute dataset](https://www.kaggle.com/datasets/henrybaylis/end-of-lane-phase-data-from-euw-apex-s15-split-2) | Full CSV: 25,346 team rows representing 12,673 matches. Listed CC BY-NC-SA 4.0. | Fourteen-minute inputs, twenty-minute regression targets, and no eventual winner field. It is not a direct replacement for the ten-minute win task. |
| [Collective Intelligence, Zenodo v2](https://zenodo.org/records/16995053) | Metadata plus header/first-row inspection. DOI 10.5281/zenodo.16995053; CC BY 4.0; associated paper and public collection code. | Excellent formal provenance, but the released aggregate table has final-match statistics and whole-game assist lists, without checkpoint timestamps. Cannot reconstruct ten-minute features from those aggregates. The paper's duration-based selection also limits the population. |
| [Chinicz summoner/match dataset](https://www.kaggle.com/datasets/chiniczr/league-of-legends-summoners-and-match-data) | Metadata and complete file inventory inspected; no multi-GB download. Collection method and [code](https://github.com/Intigram/DataCollection) documented; listed MIT. | The description explicitly identifies the match JSON as final-match data, not timelines. Its CSV is not a ten-minute dataset. Beware its inverse winner encoding: 0 means blue won. |
| [AngryBacteria match/timeline archive](https://huggingface.co/datasets/AngryBacteria/league_of_legends) | Dataset card inspected; claims over 13,000 matches, summary and per-minute timeline files, approximately 15.8 GB; listed Apache 2.0. | Potential raw alternative, but collection/sampling documentation is sparse and the storage format/size adds work. Not fully audited. |

License labels above are publisher declarations. They do not prove that the uploader has authority to license all underlying Riot material or that Riot expressly approved model training.

## Focused interval candidate: verified statistics

The derived candidate `data/intervals-2026/euw_10min_patches_16_1_16_2.csv` was constructed by:

1. Selecting `minute == 10` from `intervals.csv`.
2. Joining `player_id` and `match_id` to the player lookup. All selected player keys matched, and no duplicate match-player pairs occurred.
3. Requiring five blue players and five red players per match.
4. Summing player gold, XP, farming, kills, deaths, and assists; averaging player level. Team objective counts are repeated on player rows, so take one validated common team value rather than summing it five times.
5. Joining the match outcome and metadata. `winning_team == 100` maps to `blueWins == 1`.
6. Requiring ranked solo queue 420, duration greater than 600 seconds, an EUW1 match-ID prefix, and patches 16.1 or 16.2.
7. Excluding items, towers, and inhibitors from this initial candidate because of collection concerns. Dropping the six constant Baron/Herald columns.

Result:

- **37,631 distinct matches**, January 8-30, 2026 according to the collector's stored dates. The timezone of these naive dates is undocumented.
- **18,726 blue wins (49.76%)**, **18,905 blue losses (50.24%)**.
- **30 numeric predictor columns**: blue, red, and blue-minus-red values for ten quantities: total gold, XP, lane CS, jungle CS, kills, deaths, assists, average level, dragons, and void grubs.
- Three metadata columns (`match_id`, `game_date`, `game_version`) and the label. Metadata are retained for joins/splitting, not automatically treated as predictors.
- No missing cells in this derived candidate.
- The 30 predictors are intentionally redundant: the differences are deterministic functions of the side totals. A later modeling choice could use only differences or only side totals.
- No wards/vision features are present in this candidate. The original vision-ablation experiment would require collecting those features separately or changing the experiment to objective features.

Three real labeled examples are in `findings/three_recent_10min_examples.csv`. They include a blue win with a gold lead, a blue loss with a gold lead, and a blue win from a gold deficit. They illustrate the data; they are not performance evidence.

### Quality issues that prevent treating the interval candidate as fully validated

- **License:** the Kaggle metadata says Other (specified in description), but no explicit grant was found in the description. The linked collection repository has no identified license. Seek author clarification if selecting this dataset; no message has been sent.
- **Platform:** all match rows report `region=euw1`, but IDs include 57 EUN1 matches and one TR1 match. The focused subset uses the match-ID prefix to filter these out.
- **Patch:** `patch_version` stores only a major number such as 16. Use the first two components of `game_version` for the actual patch.
- **Rank:** the collector labels `average_rank` using the first participant's current tier. This is neither a true team average nor a verified historical rank. Do not advertise the subset as exclusively Diamond/Master or use this field without qualification.
- **Timestamp:** the collector uses frame index 10, not each frame's real timestamp. Live Riot inspection confirmed frame timestamps can be slightly after exactly 600 seconds. The published interval CSV does not retain that timestamp, preventing exact independent verification of the cutoff.
- **Towers/inhibitors:** published code increments the team identified by a BUILDING_KILL event's `teamId`. In observed raw Riot events, that is the destroyed structure's team, while the killer belongs to the opposite team. The code appears to track structures lost under fields named team_towers/team_inhibitors. This is a code-level semantic concern; historical rows were not checked against their original raw timelines.
- **Items:** the collector's ITEM_UNDO handling removes the last inventory entry rather than reconstructing the specific undo. Excluded from the derived candidate.
- **Roles:** opponent lookup uses final match role metadata, with a fallback to the player's own frame. This can produce misleading lane differences; the candidate uses independently recomputed team totals instead.

## Riot API: documented capabilities and observed fields

Official references: [Account-v1](https://developer.riotgames.com/apis#account-v1), [League-v4](https://developer.riotgames.com/apis#league-v4), [Match-v5](https://developer.riotgames.com/apis#match-v5), [routing and client documentation](https://developer.riotgames.com/docs/lol).

| API | Data/use |
| --- | --- |
| Account-v1 Riot ID lookup | Convert a known GameName#TagLine into a PUUID for a seed account. Optional when league entries already provide PUUIDs. |
| League-v4 tier/division entries | Obtain seed players from selected ranks and snapshot their current tier. The live EUW Diamond I page returned 205 entries with usable PUUIDs. |
| Match-v5 match IDs by PUUID | Paginated match discovery, with queue and timestamp filters. There is no universal endpoint for randomly sampling every ranked match. |
| Match-v5 match details | Match ID, timestamps, patch/gameVersion, platform, queue/map, participants/team membership, champions, and final winner. Use outcomes for labels and appropriate fields for static metadata; final combat/economy statistics are not checkpoint predictors. |
| Match-v5 timeline | All ten participant frames, approximately every minute, plus timestamped events. Supports multiple checkpoints from one downloaded timeline. |
| Data Dragon | Versioned static champion/item information for decoding IDs. No secret API key is needed for those static assets. |

In the live pilot, participant frames included total/current gold, XP, level, lane/jungle minions, position, champion stats, damage stats, goldPerSecond, and timeEnemySpentControlled. `damageStats` included damage done to champions and damage taken, with physical/magic/true components. Validate units before analysis; no unverified blanket damage scaling was applied.

Observed events included CHAMPION_KILL, WARD_PLACED, WARD_KILL, ELITE_MONSTER_KILL, and BUILDING_KILL. These can reconstruct cumulative KDA, wards placed/destroyed, dragons, void grubs, Herald/Baron, and structures destroyed. Item events also support inventory reconstruction, but robust handling of purchases, sales, destruction, and undo is additional work. A final visionScore is not automatically a ten-minute visionScore.

### Live pilot results

- Platform EUW1; regional routing Europe.
- Five seed PUUIDs selected from the first Diamond I page; only one seed's history was needed to find the pilot matches. This is a convenience sample, not a representative sample or a training dataset.
- **22 API requests, all HTTP 200**, yielded **10 eligible matches**. Pilot labels: three blue wins and seven losses; do not generalize that balance to the ladder.
- Observed match patches span 16.13-16.20. Sampling players by current rank does not ensure their recent matches are all on the latest patch.
- Raw match/timeline responses are cached under `private/riot/euw1/`, which is ignored for version control. Raw responses can contain player identifiers.
- Processed pilot files retain aggregate features and match metadata. No model was trained, and no data was published.

### Exactly ten minutes versus the nominal ten-minute frame

The ten nominal frames in the pilot occurred at **600.176-600.290 seconds**, rather than exactly 600.000 seconds.

- `strict` mode uses only frame/event data available by 600.000 seconds. The most recent numeric frames were at 540.168-540.261 seconds; numeric aggregates are therefore almost a minute old, while event counters are updated through 600 seconds. This is correct availability handling but not an exact, synchronized ten-minute state.
- `nominal` mode uses the nearest frame within five seconds of ten minutes and counts events through that frame's actual timestamp. In this pilot the state is synchronized at approximately 10:00.2. Both requested and actual cutoffs are stored explicitly.
- Choose and report one convention for the main dataset. For comparisons with nominal Kaggle checkpoints, the nominal frame convention is usually easier to align. For an exactly 600-second prediction rule, retain strict availability and frame age. Do not silently use a later frame while claiming all inputs came from before 600 seconds.

Both versions were generated from the same cached responses, requiring no additional network calls:

- `findings/riot-euw1-10min-strict-pilot.csv`
- `findings/riot-euw1-10min-nominal-pilot.csv`
- `findings/riot-offline-recheck.json`

## Collection plan for a course-sized dataset

- Define one platform, ranked solo queue, a date window, and allowed patches before collection.
- Select several seed players or several tier/division pages; record the procedure and sampling bias. Deduplicate match IDs across player histories.
- Retrieve match details plus timelines. Require both teams and ten participants, the chosen checkpoint, and a well-defined outcome. Document remake/aborted-game exclusions. Keep ordinary completed surrender outcomes if consistent with the task; report any different rule.
- Keep all checkpoints for a match in the same train/test group. With explicit dates, evaluate chronologically. Avoid filtering retrospectively on a long final duration to make the ten-minute task easier.
- Use team aggregate features initially. Retain role/champion details as a later extension. Retain timestamps/patches as metadata for sampling and evaluation.
- Estimate throughput from the actual rate limits returned for the issued key. The pilot client paces requests at least 1.3 seconds apart, caches responses, bounds retries, and respects Retry-After on 429.
- At that pacing, fetching two responses for each of 3,000-5,000 uncached matches takes roughly 2.2-3.6 hours before discovery, exclusions, errors, and additional metadata calls. This is a planning estimate, not a measured end-to-end collection guarantee.
- A larger sample would be a separate collection run; the current helper intentionally caps the feasibility pilot at 25 matches.

## Permitted use: evidence and open question

Riot's [LoL guidance](https://developer.riotgames.com/docs/lol) explicitly includes school projects among personal-key use cases. Its [portal documentation](https://developer.riotgames.com/docs/portal) lists personal research, explains development-key expiry after 24 hours, and requires respecting rate limits. These are evidence supporting academic API access.

The reviewed [API terms](https://developer.riotgames.com/terms) grant limited, conditional rights and do not contain an explicit model-training authorization. A publisher's CC0/MIT/CC license label and successful authenticated API requests do not themselves answer Hongyi's specific training-permission question. Report what is documented and what is still unconfirmed; request developer support clarification if the TA requires an explicit statement. No support message or dataset-author message has been sent.

## Citation records to verify/style for the final proposal

- Yi Lan Ma; 2020; League of Legends Diamond Ranked Games (10 min); Version 1; Kaggle; linked above. No verified DOI or associated originating paper identified.
- Nathan Smallcalder; 2026; LoL Match Intervals: 2 Million In-Game Snapshots; Version 2; Kaggle; linked above. No verified DOI. Include the linked collection repository and Riot API reference as provenance sources.
- Sajan Maharjan, Evangelos Pournaras, and Srijoni Majumdar; 2025; Collective Intelligence Outperforms Individual Talent: A Case Study in League of Legends; v2 dataset; Zenodo; DOI [10.5281/zenodo.16995053](https://doi.org/10.5281/zenodo.16995053). Its strong citation record does not compensate for the checkpoint mismatch.

## Local access commands

Credentials are saved outside this project. Kaggle uses the official `~/.kaggle/access_token` convention. Riot uses `%LOCALAPPDATA%\4al3\credentials\riot-api-key.txt`. The save helper prompts for hidden input and restricts file access to the current Windows user and SYSTEM. Values are not printed. Append `-Replace` when intentionally refreshing an existing key.

```powershell
& 'C:\Code\4al3\project-research\save-api-key.ps1' -Provider Kaggle
& 'C:\Code\4al3\project-research\save-api-key.ps1' -Provider Riot

& 'C:\Code\4al3\project-research\kaggle.ps1' datasets list -s 'league of legends timeline' --csv
& 'C:\Code\4al3\project-research\kaggle.ps1' datasets files nathansmallcalder/league-of-legends-match-interval-snapshots-2026

& 'C:\Code\4al3\project-research\run-riot-pilot.ps1' --platform euw1 --count 10 --checkpoint-mode nominal
```

The raw candidate files were downloaded locally during the investigation; they are not included in the public repository. `run-riot-pilot.ps1` now uses Python from the active environment (or `LEAGUE_PREDICTOR_PYTHON`), with the optional requests dependency. `kaggle.ps1` uses the installed official CLI. The absolute paths above describe the original investigation workspace; teammates can use repository-relative paths instead. Extraction logic was checked for cutoff handling, KDA, team aggregation, tower ownership, and short-game exclusion, then rechecked on the observed raw responses.

### Correction: player-list construction (October 9, 2026)
A further repository review found collect_summoners.py, a companion script referenced by the README. It starts from one configured Riot ID, fetches the last 20 matches without a queue filter, adds their participants, and expands through those participants' histories (configured depth 2). It writes summoner_names.txt for the main collector, which requests ten ranked solo-queue matches per listed player. There is no rank-based sampling or rank quota in this list-building script. This corrects the earlier statement that seed-list construction was entirely undocumented. The exact execution settings and any repeated runs used for the published dataset remain unverified. The main collector's average_rank field still records the first participant's current tier, not an average historical match rank.
Source: https://github.com/NathanSmallcalder/LeagueFiveMinIntervals/blob/main/collect_summoners.py
