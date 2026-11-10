# Project research archive

These notes and tools document the dataset investigation, proposal iterations, API feasibility pilot and report planning. They are retained for review; use the root README and latest model comparison for current experiment status.

- `research-notes.md`: source-by-source investigation, quality checks and limitations.
- `champion-and-item-project-options.md`: optional richer-context directions.
- `proposal-sections-5-and-6*.md`: historical draft iterations, not competing current specifications.
- `findings/`: computed dataset audits and aggregate pilot examples. No raw player records are included.
- `audit_datasets.py`: full alternative-dataset audit. Download the cited candidate files into its expected local `data/` directories before running it.
- `riot_pilot.py`: optional Riot feasibility collection/extraction tool. Not needed for reproducing the current models. Install `requests` separately if using it.
- `run-riot-pilot.ps1`: Windows launcher using Python from the active environment; optionally set `LEAGUE_PREDICTOR_PYTHON` to another interpreter.
- `kaggle.ps1`: Windows wrapper for the optional official Kaggle CLI (`python -m pip install kaggle`).
- `save-api-key.ps1`: optional Windows helper that saves credentials outside the checkout and never prints their values.

The local source-retrieval notes contain private course-message links and are not published. Third-party code/documentation snapshots, raw Riot JSON and larger alternative downloads also remain local. The research notes link the original public sources.
