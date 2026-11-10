# 5. Data Source

We plan to use Yi Lan Ma's _League of Legends Diamond Ranked Games (10 min)_ (2020, Version 1), hosted on [Kaggle](https://www.kaggle.com/datasets/bobbyscience/league-of-legends-diamond-ranked-games-10-min/data). The uploader identifies the original source as the [Riot Games API](https://developer.riotgames.com/apis). The dataset contains team-level statistics after the first ten minutes of each game, along with the final match outcome.

According to the uploader, these are ranked solo-queue games from high Diamond I to Master, where players have roughly similar skill levels. This is fine as long as we take into account that we'd be making predictions for high-skill brackets and not the general player base. The uploader describes the source and checkpoint, but doesn't provide collection code or a detailed account of player sampling and preprocessing. The CSV also doesn't include the server, match dates, or patch versions, so we can't restrict it to a particular region or patch.

We will use all **9,879 matches** and start with a subset of the available features. This dataset fits the core project without us first having to build a collection pipeline.

## Features and Preparation

Our main goal is to predict the probability that the blue team eventually wins, given the game state at ten minutes. The core project will use economy, experience, farming, combat, objectives, and vision. Champion and item interactions are an optional expansion if we have time and they add something useful.

This kind of probability estimate is relevant to spectator analysis and esports forecasting, including the probability questions behind sports betting. Our proposed application is match analysis, since [Riot's API policies](https://developer.riotgames.com/policies/general) don't allow betting or gambling functionality.

Each row already represents one full match, with the blue and red teams' statistics side by side. We don't need to join player tables or aggregate individual records. We can compute differential features by subtracting the red team's values from the blue team's values; gold and experience differences are already provided.

Our initial feature set tracks twelve quantities across both sides: blue-team values, red-team values, and their net differences, yielding **36 candidate numeric features** in total:

| Group | Selected quantities | Game context |
| --- | --- | --- |
| Economy | Total gold | Gold funds item purchases that strengthen champions. |
| Experience | Total XP; average level | Levels upgrade champion abilities and base attributes. |
| Farming | Lane minions and jungle monsters killed | Farming provides gold and XP. |
| Combat | Kills; deaths; assists | Reflects early skirmishes and player eliminations. |
| Objectives | Dragons; Rift Heralds | Tracks early objective control and opportunities to push lanes. |
| Vision | Wards placed; wards destroyed | Wards reveal nearby areas, helping teams spot enemies and control objectives. |

We selected this initial feature subset based on League of Legends domain knowledge regarding what features are usually impactful (two of the group members are frequent players). The original CSV has **38 predictors**, but we aren't proposing to use all of them immediately. Other available features include first blood, towers destroyed, total elite monsters killed, and gold/farming rates. Some of these overlap with the quantities above, so we'll see whether they add anything during modeling.

We will evaluate whether using only differential features performs better than retaining all three representations (blue, red, and difference). Note that feature selection is difficult without running some actual modeling first, so this set will be our initial best guess, and we're planning on modifying it as the project progresses. We'd also check whether the probabilities are reliable: if a model gives a set of games a 70% chance of winning, blue should win roughly 70% of those games.

The target label is `blueWins`: **1 if the blue team eventually won the match, and 0 if they lost**. This is taken directly from the final game result, requiring no manual labeling. All input features describe the state at minute ten, while the final outcome is reserved strictly as the ground-truth label. The `gameId` column is retained for tracking matches, rather than used as a predictor.

### Optional Expansion: Champion and Item Context

The basic features tell us who's ahead, but not necessarily what that advantage means. The same gold lead could look quite different depending on which champion holds it, what they've bought, and who they're playing against. League of Legends is a highly complex game, and an optional expansion would be to see whether adding this context improves the win-probability estimates.

**This Kaggle dataset doesn't contain champions, roles, individual player stats, or item inventories.** To try this expansion, we would collect a new set of matches through Riot's API with both the core statistics and the additional information:

| Group | Possible features | What we'd look at |
| --- | --- | --- |
| Champions and roles | All ten champion picks and their roles | Who holds the lead and how the teams are put together |
| Individual advantages | Gold, XP, and levels per player; differences between opposing roles | Whether an advantage is concentrated in a particular lane or player |
| Matchups and combinations | Opposing champion pairs and selected teammate combinations | Whether champion matchups and synergies add information beyond the scores |
| Item builds | Item inventories, unspent gold, item value, and completed-item counts | How far players have progressed through their builds and whether they've spent their gold |

Item names, prices, and build paths can be added using [Riot's patch-specific Data Dragon files](https://developer.riotgames.com/docs/lol#data-dragon). Match details provide champion picks and roles, while timeline events let us reconstruct inventories at ten minutes.

On the newly collected data, we would compare the core model with champion features, item features, and both together on the same held-out matches. The goal is to see whether the extra context actually improves predictions. The **36 candidate numeric features** above describe the core set; the expanded feature count would depend on how we represent champions and items. The details would certainly require more investigation, playing around with the data, and modelling to solidify, so for now we'd like to leave this as a potential future direction.

## Limitations

The Kaggle release already includes basic vision statistics, but omits several richer metrics available in raw Riot API responses, such as player coordinates, damage dealt to champions, and champion/item information. It also dates back to 2020, so we'd be studying games played under an older version of League rather than assuming the model applies to the current game.

On Kaggle, the dataset license is marked as **CC0: Public Domain**. Riot Games' Developer Portal lists school projects as a supported use for personal API keys. Whether our model-training use is covered still needs clarification. [Riot guidance](https://developer.riotgames.com/docs/lol) and [API terms](https://developer.riotgames.com/terms).

## Alternative: Direct Collection from Riot Games API

If we need more data, find the existing features aren't enough, or decide to try the champion/item expansion, our alternative is direct collection via the official Riot Games API. We would query `League-v4` to find seed accounts in Diamond and Master, then use `Match-v5` to retrieve recent match details and timelines on the EUW server within a single patch window. This would give us more control over the feature set, more freedom to choose seed players and rank coverage, and the ability to collect more data on demand.

API access requires a developer account and key; development keys expire after 24 hours. To respect Riot's personal-key limits of 20 requests per second and 100 per two minutes, our pipeline would pace requests, cache responses, and respect the `Retry-After` header and any additional limits returned by the API. [API access guidance](https://developer.riotgames.com/docs/portal). The downside is that this requires extra work, so if the conveniently curated dataset on Kaggle is acceptable, we'd rather use that for the core project.

# 6. Dataset Size & Example

The Kaggle CSV contains **9,879 unique matches** and **40 columns**: **38 predictors**, a match ID, and the `blueWins` label. Each row is one game's ten-minute snapshot.

There are **4,930 blue wins (49.90%)** and **4,949 blue losses (50.10%)**, providing an almost perfectly balanced binary classification target. We verified that there are no missing values or duplicate match IDs in the CSV. We plan to use all matches, so the sample comfortably exceeds the course requirement of at least 1,000 data points.

Our proposed core representation uses the twelve quantities in Section 5, with values for both teams and their differences. This gives 36 candidate numeric features after preparation, rather than simply using all 38 original predictors.

## Three Examples from the Selected Dataset

Below are three actual examples from the Kaggle CSV. For clarity, only selected differences (blue minus red) are displayed alongside the target label:

| Game ID | Gold difference | XP difference | Kill difference | Dragon difference | `blueWins` |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4475365709 | +698 | +101 | +2 | +1 | **1** |
| 4519157822 | +643 | -8 | +3 | 0 | **0** |
| 4509433346 | -1,548 | -1,574 | -1 | +1 | **1** |

## Verified API Pilot Sample

To confirm our direct collection pipeline, we gathered an exploratory pilot sample of **10 matches across 22 successful API queries** on EUW. These are separate, recent matches collected through the API, rather than extra rows from the Kaggle dataset. This confirmed our ability to extract frames at approximately ten minutes, parse events, and generate vision metrics:

| Match ID | Gold difference | XP difference | Kill difference | Wards placed diff | `blueWins` |
| --- | ---: | ---: | ---: | ---: | ---: |
| EUW1_7916252998 | -3,513 | -4,446 | -7 | +2 | **1** |
| EUW1_7916358462 | -2,449 | -1,585 | -5 | +2 | **0** |
| EUW1_7925379060 | -27 | +1,062 | 0 | +1 | **1** |

If we transition to direct collection, we plan to collect **3,000–5,000 unique matches** using seed accounts across selected high-elo tiers and divisions.

## Dataset Citation

Ma, Y. L. (2020). _League of Legends Diamond Ranked Games (10 min)_ (Version 1) [Dataset]. Kaggle. [Dataset page](https://www.kaggle.com/datasets/bobbyscience/league-of-legends-diamond-ranked-games-10-min).
