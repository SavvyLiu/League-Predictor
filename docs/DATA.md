# Data included in this repository

## Core modeling dataset

- Creator: Yi Lan Ma (`bobbyscience`).
- Title: *League of Legends Diamond Ranked Games (10 min)*, Version 1, 2020.
- [Publisher page](https://www.kaggle.com/datasets/bobbyscience/league-of-legends-diamond-ranked-games-10-min).
- Location: `progress-report/data/high_diamond_ranked_10min.csv`.
- SHA-256: `82b2e23279097c2dac616e966eb2911711c428d41b6382b4cdb15da4892f9ca6`.
- Publisher metadata lists `CC0-1.0`; this attribution is retained independently of any license decision for the team's original code.
- 9,879 distinct matches, 38 source predictors, match ID and binary winner label. There are 4,930 blue wins and 4,949 losses, with no missing cells or duplicate IDs in the checked file.

The uploader attributes collection to Riot's API and describes high-Diamond/Master solo-queue games. Dates, region, patches and player IDs are not present in the CSV. Its rank and exact checkpoint provenance cannot be independently verified from the columns. Unusually large vision values remain a quality concern.

Policy check, November 10, 2026: Riot's [API terms](https://developer.riotgames.com/terms), under Licensed Uses and Restrictions, allow documented purposes; its [Developer Portal](https://developer.riotgames.com/docs/portal#personal-api-keys) lists personal research as acceptable. We interpret offline coursework analysis as falling within that allowance. This supplies policy evidence for the TA's question without claiming project-specific approval or explicit model-training language. The publisher's CC0 label does not independently establish its authority over third-party rights. Our experiment uses only the static aggregate table, with no player identifiers or live assistance. Public player-facing deployment is a separate scope governed by Riot's [League developer policy](https://developer.riotgames.com/docs/lol#registration).

## Other investigated sources

The research notes document the interval-snapshot, post-match/timeline, Apex 14-minute and other candidate datasets. Larger downloaded files and third-party source snapshots are not part of this repository. Source links and independently computed audit summaries are retained. To rerun `project-research/audit_datasets.py`, obtain the documented candidates under its expected `project-research/data/` folders first.

## Riot feasibility pilot

The ten-match pilot is separate from the Kaggle model-training dataset. `project-research/findings/` contains aggregate feature examples and audit summaries. Raw match/timeline responses and player identifiers remain outside version control. The pilot does not establish prediction performance and is not merged into the core experiment.

API credentials are unnecessary for reproducing the report experiments. Optional collection should use personal credentials through `RIOT_API_KEY` or the documented local credential store; never place them in tracked files.
