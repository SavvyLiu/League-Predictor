# League Predictor

Group 27's machine-learning project: predict the probability that the blue team eventually wins a League of Legends match from its ten-minute game state.

**Current status:** preliminary logistic-regression and random-forest experiments are complete. All reported scores are validation results; the final test set remains reserved. The comparison is ready for TA/team discussion before further scope or data changes.

## Start here

- [Progress report (PDF)](progress-report/Group27_ProgressReport.pdf): updated November 10 with both model families, contributions, dated responsibilities and AI disclosure.
- [Model comparison brief (PDF)](progress-report/Group27_Model_Comparison.pdf): one-page summary for discussion.
- [Detailed comparison](progress-report/MODEL_COMPARISON.md): settings, uncertainty, limitations and questions for the TA.
- [Executed experiment walkthrough](progress-report/Experiment_Walkthrough.ipynb): step-by-step explanations and saved outputs.
- [Experiment guide](progress-report/README.md): reproducibility instructions, file descriptions and assumptions.
- [Original proposal](Project%20Proposal.docx) and [research notes](project-research/research-notes.md).
- [Report source](progress-report/report/main.tex) and [build instructions](docs/REPORT.md).

## Reproduce the experiments

Use Python 3.12. From the repository root:

```sh
python -m venv .venv
# Activate the environment for your shell, then:
python -m pip install -r progress-report/requirements.txt
python progress-report/code/run_experiments.py
python progress-report/code/run_random_forest.py
python progress-report/code/verify_results.py
```

The code resolves input/output paths from its own location. No API key, GPU, fresh data collection or notebook server is required for these runs. The notebook additionally requires Jupyter and a kernel containing the experiment dependencies.

Saved match allocations are reused: **6,915 train / 1,482 validation / 1,482 reserved test**, stratified with seed 42. Logistic scalers are fitted using training rows only. Forests use unscaled differences. There is no test-performance evaluation step.

## Current results

| Model | Features | Validation accuracy | ROC-AUC | Log loss |
| --- | --- | ---: | ---: | ---: |
| Majority baseline | None | 50.07% | - | - |
| Logistic regression | Gold only | 71.05% | 0.7926 | 0.54958 |
| Logistic regression | Core | 71.93% | 0.7985 | 0.54331 |
| Random forest | Core | 71.79% | 0.7965 | 0.54571 |
| Logistic regression | Core + objectives | 72.27% | 0.8006 | 0.53969 |
| Logistic regression | Core + objectives + vision | 72.13% | 0.8004 | 0.53990 |
| Random forest | Core + objectives + vision | 71.86% | 0.8004 | 0.54012 |

The tested forest has no clear advantage over the matched logistic models. The small model-family accuracy differences have paired validation-bootstrap intervals that include zero. These are initial fixed configurations, not tuned optima. See the detailed comparison for probability errors, interval assumptions and the original feature ablations.

## Repository layout

```text
progress-report/
  code/                  # fitting, forest comparison and independent checks
  data/                  # the CSV used by the core experiment and its source note
  results/               # fixed splits, validation predictions, scores and figures
  report/                # editable LaTeX report, bibliography and build helper
  Experiment_Walkthrough.ipynb
project-research/
  findings/              # dataset audits and aggregate API feasibility results
  *.md                   # research, proposal iterations and planning notes
  *.py, *.ps1            # optional audit/API tooling
docs/                    # collaboration, data and report-build notes
```

The larger alternative downloads, raw Riot responses, credentials, course handouts, private source-retrieval notes, unrelated homework and temporary build outputs remain local. Historical research notes describe work at their recorded dates; the latest comparison is in `progress-report/MODEL_COMPARISON.md`.

## Data and attribution

The core CSV contains 9,879 matches from Yi Lan Ma's *League of Legends Diamond Ranked Games (10 min)*, Version 1 (2020), [published on Kaggle](https://www.kaggle.com/datasets/bobbyscience/league-of-legends-diamond-ranked-games-10-min). The downloaded publisher metadata lists CC0. See [data notes](docs/DATA.md) for provenance, limitations and the distinction between this dataset and the separate Riot feasibility pilot.

## Collaboration

See [CONTRIBUTING.md](CONTRIBUTING.md). Please propose changes on branches and use pull requests so the team can review experiment changes. Keep the saved test set reserved. Public readers can fork and propose pull requests; direct pushes require repository write access.

Registered group members: Savvy Liu, Peter Li and Krish Panchal. The report records the contributions confirmed by Savvy: a three-way proposal split, code/report implementation by Savvy with disclosed AI assistance, and review/approval by Peter and Krish. The initial import is a repository snapshot, not a reconstruction of who completed each historical task.
