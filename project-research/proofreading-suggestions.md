# Suggested Edits to Your Revision

These are proposed changes for discussion. The revision file retains your wording, and the champion/item feature plan has not been added to it.

| Passage | Suggested change | Reason |
| --- | --- | --- |
| Player discovery follows the main collection step | Explain that a separate script builds the player list by following teammates and opponents, then the main collector retrieves ten ranked matches per player. | This matches the published scripts. |
| Diamond and above account for ~92% of the dataset | Say “about 92% of our filtered subset have a recorded rank of Diamond or above.” | The full release is about 89%. The field records the first participant's current tier, not a historical match average. |
| “limiting the patch window ensures comparable gameplay conditions” | Use “limiting the patch window reduces variation in gameplay conditions.” | Two patches still have balance differences. |
| “This specific dataset is specific to the EUW server…” and the North America comparison | Replace with “We chose this release because it provides the checkpoint data we need and inspectable collection code.” | Avoids repetition and unsupported claims about regional strength and dataset availability. |
| “complete, uncorrupted records” | Use “complete records for all ten players.” | Completeness was checked; a broader claim about data correctness has not been established. |
| Farming as “the primary recurring source” and objectives as “permanent neutral team buffs” | Use “Farming provides gold and experience” and “These track early control of neutral objectives.” | Clearer wording without unnecessary claims about every role or objective. |
| “real-time player coordinates” | Use “player positions at each timeline frame.” | Historical timelines contain snapshots, not a continuous live feed. |
| Permission paragraph | Say Riot lists school projects as a supported personal-key use case, while the uploader's license and this model-training use still need clarification. Link Riot's guidance and API terms. | Supported API access does not resolve the dataset's “Other” license or the TA's specific training-permission question. |
| “no missing values or duplicate entries” | Specify “no missing values in the 30 derived numeric features and no duplicate match-player observations at ten minutes.” | Those are the checks actually completed. New champion/item columns may need their own handling. |
| “three representative examples” | Use “three actual examples.” | The examples were chosen to illustrate inputs and outcomes, not sampled to represent the population. |
| “synchronized 10-minute frames” | Use “frames and events at approximately ten minutes.” | The pilot frames occurred about 0.2 seconds after ten minutes. |
| “scrape” | Use “collect through the API.” | More precise description of the collection method. |

The regional sentence is the main tone issue. Elsewhere, the draft is readable; shortening phrases such as “Note that feature selection is difficult…” is optional. We can discuss the feature direction before rewriting that section.

Sources: [player-list script](https://github.com/NathanSmallcalder/LeagueFiveMinIntervals/blob/main/collect_summoners.py), [main collector](https://github.com/NathanSmallcalder/LeagueFiveMinIntervals/blob/main/DataCollector.py), [Riot project guidance](https://developer.riotgames.com/docs/lol), [API terms](https://developer.riotgames.com/terms).
