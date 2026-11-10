# Champion and Item Context: Project Options

## A More Interesting Research Question

Can champion matchups, team composition, and item choices improve ten-minute win-probability predictions beyond gold, experience, and objectives?

This keeps our original target: the probability that the blue team eventually wins. The economic features become a baseline against which we test whether game context adds useful information.

For example, two teams can have the same total gold lead while that lead belongs to different champions or roles. A player who has completed an important item may also be in a different position from someone with similar total gold who has not spent it yet. The model would investigate these distinctions rather than assume they have a particular effect.

## Features We Already Have

The Kaggle tables can be joined to retain each player's champion, role, team, and checkpoint statistics instead of immediately reducing everything to team totals.

| Information | Available data | What we could investigate |
| --- | --- | --- |
| Champion choices | Champion identity for all ten players | Whether the same early lead means something different for different champions. |
| Roles and matchups | Top, jungle, mid, bottom, and support assignments | Which lane or role holds the advantage, and which champions face each other. |
| Individual performance | Gold, XP, level, farming, kills, deaths, and assists per player | Whether distributing resources differently changes the prediction. |
| Items at the checkpoint | Seven item-ID fields per player | Champion-item combinations, completed items, components, and defensive purchases. |
| Unspent gold | Current gold alongside total gold | Whether a lead has been converted into items. |
| Earlier checkpoints | Five-minute snapshots as well as ten-minute snapshots | Whether the lead grew or shrank during the previous five minutes. |

Our selected subset includes 172 champions and 184 nonzero item IDs at ten minutes. Champion identities are present for every player; three player records lack a role assignment. We can handle those records explicitly when arranging players by role.

For planning, we will use the existing item fields. If they prove unsuitable during implementation, we can collect equivalent match timelines directly through Riot's API.

## Four Possible Directions

### 1. Who Holds the Lead?

Retain each player's champion, role, gold, experience, and level. Compare gold and XP across opposing roles, and measure how much of each team's resources are concentrated in its richest players.

Questions include whether a gold lead on a damage dealer predicts differently from the same lead on another role, and whether champion identity changes how an early advantage relates to the final outcome. This is the easiest extension because the necessary data is already available.

### 2. Champion Matchups and Team Composition

Include the ten champion choices, opposing lane pairs, and selected teammate pairs. We could also add a small, documented set of champion categories, such as ranged/melee, frontline, or damage type, to describe broader team compositions.

The goal is to test whether matchups and combinations add information beyond the current scores. For example, we could compare predictions for similar gold leads held by different compositions. Labels such as engage strength or late-game scaling would need our own definitions; they are not ready-made Kaggle columns.

### 3. Item and Champion Context

Represent each player's inventory together with champion identity and current resources. Possible features include specific champion-item combinations, item categories, inventory value, unspent gold, and completed-item counts.

[Riot's Data Dragon](https://developer.riotgames.com/docs/lol#data-dragon) provides patch-specific item names, prices, build paths, descriptions, and stats. These let us translate item IDs into useful features. Some effects and champion interactions would need additional interpretation rather than a simple sum of item stats.

This would let us investigate questions such as whether item information improves predictions among games with similar gold totals, or whether defensive purchases matter differently against different opposing compositions. The Kaggle snapshots support inventories at a checkpoint, but not exact purchase timestamps or the full purchase sequence. Those would require direct timeline collection.

### 4. How the Advantage Developed

Add changes from minute five to minute ten: gold and XP gained, changes in role advantages, objective acquisition, and changes in item inventories.

This could distinguish teams with the same ten-minute score but different recent trajectories. We would still predict at ten minutes, using only observations available by that point. All observations of a match must stay in the same training, validation, or test partition.

## Recommended Course Scope

Start with one study of champion and item context, using the existing dataset:

1. **Baseline:** team economy, combat, farming, and objectives.
2. **Champion extension:** baseline plus champions, roles, individual statistics, and role matchups.
3. **Item extension:** baseline plus inventories, unspent gold, and item summaries.
4. **Combined model:** baseline plus champion and item context.

Compare these on the same held-out matches, preferably using a chronological split. Since we are predicting probabilities, compare log loss, Brier score, and calibration as well as classification performance. A model that adds context should demonstrate improvement on unseen games; extra columns alone are not a result.

A regularized classifier can establish the baseline, with a categorical tree model such as [CatBoost](https://catboost.ai/docs/en/features/categorical-features) as one option for champion and item categories. Any win-rate or matchup summaries used as inputs must be calculated from training data only.

There are enough games for this comparison, but not for reliable statistics on every possible champion/item combination. In the selected data, the median observed opposing champion pair has only two to four matches, depending on role. We should share information across champions and item categories, and avoid treating each complete ten-champion draft as a separate category.

## What the Finished System Could Show

A small post-game analysis view could accept or display a ten-minute snapshot, show the predicted blue-team win probability, and summarize which observed features most influenced the model. It could also show how the baseline prediction differs from the prediction with champion and item context.

This fits the spirit of [iTero's drafting analysis](https://itero-website.vercel.app/articles/the-draft-model), which discusses counter matchups and champion synergies. It gives our project a focused question to investigate rather than trying to reproduce an entire coaching platform.

An item recommendation system is a possible later extension, but a win predictor does not by itself establish which purchase would improve a player's outcome. For example, a particular item might appear in winning games because players buy it when already ahead. Model comparisons and feature explanations describe predictive associations, not proven benefits from changing a build.
