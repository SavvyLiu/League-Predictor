# Collaborating on League Predictor

1. Clone the repository, or fork it if you do not have write access.
2. Create a branch for the change, such as `experiment/forest-depth` or `report/results-discussion`.
3. Explain the question being tested and the feature/model choices before changing experiments.
4. Run the reproduction commands in the root README and `verify_results.py` when changing model or evaluation code.
5. Open a pull request describing the change, measured results, and limitations. Report edits can be reviewed without rerunning unchanged models.

## Experiment rules

- Preserve `results/split_assignments.csv`. Keep the same matches for a controlled comparison.
- Fit all learned preprocessing, tuning and calibration on training data/folds only.
- Do not evaluate final test performance during model development. Allocation/label-count checks do not authorize using the test set for model selection.
- Record feature columns, seeds, settings, versions and whether values were selected after viewing validation results.
- Keep the original measured results. Use separate output directories or files for new configurations instead of relabeling old scores.
- Explain negative or small results; do not omit runs simply because they fail to improve accuracy.
- Attribute actual human contributions and disclose AI assistance as required by the course.

## Files and data

Do not commit credentials, session files, raw player identifiers, personal chat exports, course handouts or unrelated assignments. The ignore rules preserve these local files while tracking the project work. Optional API tooling uses your own credentials stored outside the repository; the core modeling work requires none.

The checked CSV is included. Larger alternative datasets are documented by source links and audit summaries; fetch them separately if the team decides to investigate them. Do not add new datasets to the repository before checking size, provenance and the team's intended use.

## Report status

The November 10 report integrates the logistic/forest results and includes confirmed contributions, dated responsibilities and the scoped AI-use estimate. See [report build notes](docs/REPORT.md) for template dependencies, table generation and packaging. Preserve the distinction between validation findings and the reserved final test.
