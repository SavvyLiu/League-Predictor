# 5. Data Source

We plan to use Nathan Smallcalder's _LoL Match Intervals: 2 Million In-Game Snapshots_ (2026, Version 2), hosted on [Kaggle](https://www.kaggle.com/datasets/nathansmallcalder/league-of-legends-match-interval-snapshots-2026). The underlying data originates from [Riot Games' Match-v5 API](https://developer.riotgames.com/apis#match-v5), and the uploader provides their [data collection script on GitHub](https://github.com/NathanSmallcalder/LeagueFiveMinIntervals/blob/main/DataCollector.py). The dataset contains player-level performance statistics at five-minute intervals, final match outcomes, and match metadata including game version, dates, team assignments, and champion picks. More details on feature selection follow below.

It looks like the collection script pulls ten recent ranked solo-queue matches for each player in a seed list, deduplicates match IDs, and parses event timelines. A [separate script](https://github.com/NathanSmallcalder/LeagueFiveMinIntervals/blob/main/collect_summoners.py) builds the seed list by finding teammates and opponents in recent match histories and following their histories too. It appears the resulting rank distribution of the dataset may be sensitive to the initial seed players chosen. An inspection of the dataset shows a skew towards higher ranks (Diamond and above account for ~92% of our filtered subset, based on the first participant's recorded rank). This is fine as long as we take into account that we'd be making predictions for high-skill brackets and not the general player base.

To ensure consistency, we restrict our dataset to ten-minute snapshots from the Europe West (EUW) server on patches 16.1 and 16.2. Because balance patches alter champion power and game pacing, limiting the patch window ensures comparable gameplay conditions. This dataset is almost entirely from EUW, and it was chosen because North America is historically inferior at the game and we didn't find suitable checkpoint data from other strong servers like Korea or China. We filter for matches that lasted longer than ten minutes and have complete, uncorrupted records for all ten players (five per team).

## Features and Preparation

Our main goal is to predict the probability that the blue team eventually wins, given the game state at ten minutes. The core project will use economy, experience, farming, combat, and objectives. Champion and item interactions are an optional expansion if we have time and they add something useful.

This kind of probability estimate is relevant to spectator analysis and esports forecasting, including the probability questions behind sports betting. Our proposed application is match analysis, since [Riot's API policies](https://developer.riotgames.com/policies/general) don't allow betting or gambling functionality.

We join the snapshot, player, and match tables so that each row represents one full match. Player-level statistics are aggregated into team totals, with the exception of champion level, which is averaged across the five players. Neutral objectives (such as dragons) are already tracked at the team level, so they are recorded once per side. Finally, we compute differential features by subtracting the red team's totals from the blue team's totals.

Our core feature set tracks ten key metrics across both sides: blue-team values, red-team values, and their net differences, yielding **30 numeric features** in total:

| Group      | Selected quantities                     | Game context                                                   |
| ---------- | --------------------------------------- | -------------------------------------------------------------- |
| Economy    | Total gold                              | Gold funds item purchases that directly scale champion stats.  |
| Experience | Total XP; average level                 | Levels upgrade champion abilities and base attributes.         |
| Farming    | Lane minions and jungle monsters killed | Minion farming is the primary recurring source of gold and XP. |
| Combat     | Kills; deaths; assists                  | Reflects early skirmishes and player eliminations.             |
| Objectives | Dragons; void grubs                     | Tracks early control of permanent neutral team buffs.          |

We selected this core feature subset based on League of Legends domain knowledge regarding what features are usually impactful (two of the group members are frequent players). Objectives like Baron Nashor and Rift Herald do not spawn before minute 10, so their counts are zero across all matches and were removed. We will evaluate whether using only differential features performs better than retaining all three representations (blue, red, and difference) during baseline modeling. Note that feature selection is difficult without running some actual modeling first, so this set will be our initial best guess, and we're planning on modifying it as the project progresses.

The target label is `blueWins`: **1 if the blue team eventually won the match, and 0 if they lost**. This is taken directly from the final game result, requiring no manual labeling. All input features reflect the state at minute ten, while the final outcome is reserved strictly as the ground-truth label. Match IDs, dates, and patch versions are retained as metadata for evaluation and grouping.

### Optional Expansion: Champion and Item Context

The basic features tell us who's ahead, but not necessarily what that advantage means. The same gold lead could look quite different depending on which champion holds it, what they've bought, and who they're playing against. League of Legends is a highly complex game, and an optional expansion would be to see whether adding this context improves the win-probability estimates.

The Kaggle files already contain the champion, role, individual stats, and item inventories needed to try this. We would keep player-level information alongside the team totals and add:

| Group | Possible features | What we'd look at |
| --- | --- | --- |
| Champions and roles | All ten champion picks and their roles | Who holds the lead and how the teams are put together |
| Individual advantages | Gold, XP, and levels per player; differences between opposing roles | Whether an advantage is concentrated in a particular lane or player |
| Matchups and combinations | Opposing champion pairs and selected teammate combinations | Whether champion matchups and synergies add information beyond the scores |
| Item builds | Item inventories, unspent gold, item value, and completed-item counts | How far players have progressed through their builds and whether they've spent their gold |

Item names, prices, and build paths can be added using [Riot's patch-specific Data Dragon files](https://developer.riotgames.com/docs/lol#data-dragon). For now, we're planning around the item data already in Kaggle; if it turns out to be lacking, we can collect timelines directly through the API.

We would compare the core model with champion features, item features, and both together on the same held-out matches. The goal is to see whether the extra context actually improves predictions. We'd also check whether the probabilities are reliable: if a model gives a set of games a 70% chance of winning, blue should win roughly 70% of those games. The **30 numeric features** above describe the core set; the expanded feature count would depend on how we represent champions and items. The details would certainly require more investigation, playing around with the data, and modelling to solidify, so for now we'd like to leave this as a potential future direction. 

## Limitations

While convenient, the Kaggle release omits several rich metrics available in raw Riot API responses, such as player coordinates at each timeline frame, damage dealt to champions, and warding events.

On Kaggle, the dataset license is marked as "Other" without an explicit reuse grant. Riot Games' Developer Portal lists school projects as a supported use for personal API keys. We still need to clarify the dataset's reuse license and whether our model-training use is covered. [Riot guidance](https://developer.riotgames.com/docs/lol) and [API terms](https://developer.riotgames.com/terms).

## Alternative: Direct Collection from Riot Games API

If we need more data, find the existing features aren't enough, or decide to incorporate vision and positioning data, our alternative is direct collection via the official Riot Games API. We would query `League-v4` to seed player accounts across specific ranked tiers, then use `Match-v5` to retrieve recent match details and 10-minute timelines on the EUW server within a single patch window. This would give us more control over the feature set (that the Kaggle dataset was missing), more freedom to choose seed players and rank distributions, and the ability to collect more data on demand. API access requires a developer account and key; development keys expire after 24 hours. To respect Riot's personal key rate limits of 20 req/s and 100 req/2 min, our pipeline would use conventional request pacing and respect the Retry-After header. The downside is that this requires extra work, so if the conveniently curated dataset on Kaggle is acceptable, we'd rather use that.

# 6. Dataset Size & Example

The full Kaggle archive contains **39,954 matches** and **2,108,090 player-interval rows** (which represent repeated 5-minute snapshots of players within games, not 2 million independent matches).

Our filtered ten-minute subset contains **37,631 unique matches** played between January 8 and January 30, 2026. The dataset has **18,726 blue wins (49.76%)** and **18,905 blue losses (50.24%)**, providing an almost perfectly balanced binary classification target. We verified that there are no missing values in the derived core features or duplicate match records. This sample size comfortably exceeds the course requirement of at least 1,000 data points.

## Three Examples from the Selected Dataset

Below are three representative examples from our filtered dataset. For clarity, only key differential features (blue minus red) are displayed alongside the target label:

| Match ID        | Gold difference | XP difference | Kill difference | Dragon difference | `blueWins` |
| :-------------- | --------------: | ------------: | --------------: | ----------------: | :--------: |
| EUW1_7675563128 |          +2,247 |          +907 |              +5 |                +1 |   **1**    |
| EUW1_7675561720 |          +1,001 |          +877 |               0 |                +1 |   **0**    |
| EUW1_7675600132 |          -1,431 |          +702 |              -2 |                 0 |   **1**    |

## Verified API Pilot Sample

To confirm our direct collection pipeline, we gathered an exploratory pilot sample of **10 matches across 22 successful API queries** on EUW. This confirmed our ability to extract frames at approximately ten minutes, parse events, and generate vision metrics:

| Match ID        | Gold difference | XP difference | Kill difference | Wards placed diff | `blueWins` |
| :-------------- | --------------: | ------------: | --------------: | ----------------: | :--------: |
| EUW1_7916252998 |          -3,513 |        -4,446 |              -7 |                +2 |   **1**    |
| EUW1_7916358462 |          -2,449 |        -1,585 |              -5 |                +2 |   **0**    |
| EUW1_7925379060 |             -27 |        +1,062 |               0 |                +1 |   **1**    |

If we transition to direct collection, we plan to collect **3,000–5,000 unique matches** using stratified seed accounts across high-elo divisions.

## Dataset Citation

Smallcalder, N. (2026). _LoL Match Intervals: 2 Million In-Game Snapshots_ (Version 2) [Dataset]. Kaggle. https://www.kaggle.com/datasets/nathansmallcalder/league-of-legends-match-interval-snapshots-2026
