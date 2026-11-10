# NA1 starter collection: verified November 10, 2026

This is a source-data feasibility check for the richer project, not a training dataset or model-performance result.

- **10 complete match/timeline pairs** accepted and independently checked.
- Platform NA1, ranked solo queue 420, Summoner's Rift map 11.
- All ten matches report game version **16.22.834.8910**, matching the collection's pinned **16.22** patch. Regional Data Dragon realm version at creation was **16.22.1**.
- Observed match starts span November 8-10, 2026 (UTC).
- All ten players' numeric frames, champion IDs, team mappings and final outcomes were checked for every pair. The sample contains **70 distinct champion IDs**.
- Nominal ten-minute frames occurred at **600.116-600.293 seconds**. These are near-ten-minute frames, not observations available strictly before 600.000 seconds.
- Through those nominal cutoffs, cached timelines contain **937 purchases, 44 item undo events, 513 item destruction events and 8 item sales**, among other combat/objective/vision events. These are event counts, not validated inventories.
- Outcomes: eight blue wins and two red wins. This small convenience sample does not establish population class balance.
- The successful live run used **31 API requests, all HTTP 200**. The manifest retains observed application/method limits.
- Repeating the completed ten-match target made **zero API requests**. Another 36 candidate IDs remain pending in the private deduplicated queue.
- Seven offline checks pass, covering cache-only operation, per-request key reload, auth rejection, request budgets, rate-limit backoff and basic eligibility filters.

The initial discovery uses ten evenly spaced current Diamond I seeds from one league page, then orders pending match IDs descending. This is a convenience sample with player/recency bias; it is not random sampling of the NA1 ranked population, and does not establish every participant's rank at match time.

Raw API responses, seed identities and the progress database remain local under ignored `private/na1-current/`. No raw player data or credentials are published. The cached source responses preserve the evidence needed for later inventory reconstruction and champion/role/trajectory features; those transformations and new-model training have not yet been implemented.

Next implementation step: build and verify a timestamp-aware checkpoint extractor, including item purchase/sale/destruction/undo semantics, before scaling collection or fitting models. Keep final-match item slots and post-checkpoint statistics out of checkpoint predictors. Decide whether the prediction boundary is strict 600 seconds or a recorded nominal frame before constructing the new training table.
