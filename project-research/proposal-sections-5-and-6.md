# 5. Data Source

We plan to use Nathan Smallcalder's *LoL Match Intervals: 2 Million In-Game Snapshots* (2026, Version 2), available on [Kaggle](https://www.kaggle.com/datasets/nathansmallcalder/league-of-legends-match-interval-snapshots-2026). The original source is [Riot Games' API](https://developer.riotgames.com/apis#match-v5), and the uploader shares [the collection code](https://github.com/NathanSmallcalder/LeagueFiveMinIntervals/blob/main/DataCollector.py). The release contains player statistics at five-minute intervals, match outcomes, and metadata such as dates, game versions, team membership, and champion choices.

The uploader's [player-list script](https://github.com/NathanSmallcalder/LeagueFiveMinIntervals/blob/main/collect_summoners.py) starts with one player and expands the list through teammates and opponents in recent matches. The main collector then retrieves ten recent ranked solo-queue matches per listed player, removes duplicate matches, and extracts timeline statistics and events. This broadens the player pool, but the code does not select a quota from each rank or establish representative rank coverage.

We will use the ten-minute snapshots from the Europe West server on patches 16.1 and 16.2. Patches change the game's balance, so limiting the patch range helps keep game conditions comparable. We retain matches that lasted more than ten minutes and have complete records for both five-player teams.

## Features and Preparation

We join the snapshot, player, and match tables to produce **one example per match**. Player statistics are summed into team totals, except champion level, which is averaged. Objective counts already describe the whole team and are counted once. We then calculate blue-minus-red differences; blue and red identify the two opposing teams.

Our initial feature set uses ten quantities, represented as blue-team values, red-team values, and their differences: **30 numeric columns** in total.

| Group | Selected quantities | Game context |
| --- | --- | --- |
| Economy | Total gold | Gold buys items that strengthen champions. |
| Experience | Total XP; average level | Levels improve champions' abilities and stats. |
| Farming | Lane minions and jungle monsters killed | Farming is a regular source of gold and experience. |
| Combat | Kills; deaths; assists | These describe how early fights have gone. |
| Objectives | Dragons; void grubs | These track control of neutral objectives. |

Gold and experience are useful starting points because they affect champion strength, while kills alone may miss advantages gained through farming. [Riot's game guide](https://www.leagueoflegends.com/en-us/how-to-play/) explains these mechanics.

This is **a subset of the Kaggle features**, chosen using our experience playing the game. We have not run models yet, so we will revise the selection as we explore the data and compare validation results. Other available features include unspent gold, dragon types, items, and champion choices. We may also use team differences instead of all three representations to avoid redundant inputs. Baron and Rift Herald counts were constant at this checkpoint and were removed.

The label is `blueWins`: **1 for an eventual blue-team win and 0 for a loss**. It comes from the recorded match outcome, so no manual labeling is needed. Predictors use the ten-minute game state; the final outcome supplies only the label. Match IDs, dates, and patches are retained as metadata.

## Limitations and Permission

The Kaggle files contain only part of what Riot's API offers. Our API pilot also returned player positions, damage statistics, and ward events, which this release lacks. Wards give teams information about otherwise hidden areas of the map, so their absence limits what we can study about vision.

We excluded item and building-destruction features because the collector's handling of these events needs checking. The recorded rank is one player's current rank, not the match's average rank. The snapshots also lack exact timestamps, so the checkpoint is approximately ten minutes.

Kaggle lists the license as **“Other,”** without a clear reuse grant. Riot's [documentation](https://developer.riotgames.com/docs/lol) supports school projects, but permission for this model-training use still needs clarification under its [API terms](https://developer.riotgames.com/terms). We will clarify the dataset license and permitted use before training.

## Alternative: Collect Directly from Riot

Direct collection would let us check timestamps and add features missing from Kaggle. We would collect recent ranked solo-queue matches from multiple EUW players, choose a fixed date and patch range, remove duplicate matches, and apply the same team-completeness and duration filters. Match-v5 provides outcomes and timelines; League-v4 provides ranked-player lists to start the collection. This would still be a sample drawn from player histories, rather than a random sample of all matches.

We would extract statistics and events at approximately ten minutes, keeping the actual timestamp. API access requires a developer account and key. Development keys expire after 24 hours; personal keys have published limits of 20 requests per second and 100 per two minutes. We will follow the limits returned by the API, cache responses, and respect `Retry-After` when rate-limited. [Riot API access guidance](https://developer.riotgames.com/docs/portal)

# 6. Dataset Size & Example

The full release contains **39,954 matches** and **2,108,090 player-time rows**. Those rows are repeated observations of players within matches, not two million independent games.

Our filtered subset contains **37,631 matches**, dated January 8–30, 2026, with **30 initial numeric predictors**. It has **18,726 blue wins (49.76%)** and **18,905 losses (50.24%)**, giving an almost even label balance. We found no missing values in the derived features, duplicate match-player snapshots, or unmatched lookup records. This comfortably exceeds the requirement of 1,000 examples.

## Three Examples from the Selected Dataset

These are actual labeled examples. Only a few inputs are shown; each difference is blue minus red. An early lead does not guarantee the final result, as the second example illustrates.

| Match ID | Gold difference | XP difference | Kill difference | Dragon difference | `blueWins` |
| --- | ---: | ---: | ---: | ---: | ---: |
| EUW1_7675563128 | 2,247 | 907 | 5 | 1 | 1 |
| EUW1_7675561720 | 1,001 | 877 | 0 | 1 | 0 |
| EUW1_7675600132 | -1,431 | 702 | -2 | 0 | 1 |

## API Collection Sample

We collected **ten usable matches through 22 successful API requests**, confirming that we can retrieve outcomes and build features. Three examples are shown below; the [full ten-row sample](/C:/Code/4al3/project-research/findings/riot-euw1-10min-nominal-pilot.csv) is saved separately. These frames occurred approximately 0.2 seconds after ten minutes.

| Match ID | Gold difference | XP difference | Kill difference | Wards placed difference | `blueWins` |
| --- | ---: | ---: | ---: | ---: | ---: |
| EUW1_7916252998 | -3,513 | -4,446 | -7 | 2 | 1 |
| EUW1_7916358462 | -2,449 | -1,585 | -5 | 2 | 0 |
| EUW1_7925379060 | -27 | 1,062 | 0 | 1 | 1 |

The pilot comes from one player's history and is only a collection check. If we switch to the API, we will target **3,000–5,000 distinct matches** from a broader set of players. The permission question above applies to direct collection too.

## Dataset Citation

Smallcalder, N. (2026). *LoL Match Intervals: 2 Million In-Game Snapshots* (Version 2) [Dataset]. Kaggle. [Dataset page](https://www.kaggle.com/datasets/nathansmallcalder/league-of-legends-match-interval-snapshots-2026).
