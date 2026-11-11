# Group 27 - League of Legends progress-report experiments

Predict eventual blue-team victory from a historical ten-minute game snapshot.

## Reproduce

Python 3.12 was used. From this folder:

```powershell
python -m pip install -r requirements.txt
python code/run_experiments.py
python code/run_random_forest.py
python code/verify_results.py
```

The script works from any current directory; paths are resolved relative to its location. It runs in seconds on this computer after imports. `Experiment_Walkthrough.ipynb` provides a readable explanation and a worked core-model example. The notebook additionally requires Jupyter, `nbformat`, and a Python kernel with the listed dependencies.

## Design choices

- One row is one match. `blueWins=1` means blue eventually wins; `0` means red wins.
- Use the original downloaded Kaggle dataset, 9,879 matches. It is included under `data/`.
- Blue-minus-red differences represent advantages. All experiments use the same matches.
- Seed 42, stratified 70/15/15 split: 6,915 training, 1,482 validation, 1,482 reserved test matches. Split assignments are saved and reused.
- The test set is not evaluated by this script. Allocation and label counts may be checked, but there are no test predictions or test performance scores.
- Models: majority class; constant training win probability; L2 logistic regression with gold only, seven core features, core plus objectives, core plus vision, and all eleven features; random forests with core and expanded features.
- Logistic models learn scalers from training rows only. Forests use raw differences. No imputation, row filtering, clipping, augmentation, class weighting, or oversampling is applied.
- Forests use 500 trees, depth at most 8, minimum 10 samples per leaf, square-root feature subsampling, bootstrap sampling, Gini splits and seed 42. These settings were fixed before inspecting forest scores; no forest tuning has been run.
- Logistic regression uses `C=1`, `solver='lbfgs'`, `tol=1e-6`, `max_iter=2000`. Hyperparameters and the 0.5 decision threshold are fixed; no search/CV or post-hoc calibration has been run.
- Retain extreme observed ward counts provisionally. No source-level verification establishes whether these are errors; they are a data-quality limitation, not verified valid behavior.
- The majority classifier has no probability-quality metrics. The constant-probability baseline supplies meaningful Brier/log-loss comparisons.
- Precision, recall and F1 use blue as the positive class. For a baseline that never predicts blue, zero precision is the explicit `zero_division=0` convention.
- Calibration diagrams use ten equal-width probability bins. They are descriptive; they do not establish calibration statistically.
- A paired 2,000-resample bootstrap compares expanded minus core predictions on validation rows. Intervals are conditional on fixed models and do not measure training/split variability or adjust for the inspected comparisons.

## Results

| Model | Accuracy | ROC-AUC | Brier | Log loss |
| --- | ---: | ---: | ---: | ---: |
| Majority class | 0.5007 | - | - | - |
| Training win probability | 0.5007 | 0.5000 | 0.2500 | 0.6931 |
| Gold only | 0.7105 | 0.7926 | 0.1861 | 0.5496 |
| Core | 0.7193 | 0.7985 | 0.1836 | 0.5433 |
| Core + objectives | 0.7227 | 0.8006 | 0.1828 | 0.5397 |
| Core + vision | 0.7193 | 0.7984 | 0.1836 | 0.5434 |
| Core + objectives + vision | 0.7213 | 0.8004 | 0.1828 | 0.5399 |
| Random forest: core | 0.7179 | 0.7965 | 0.1844 | 0.5457 |
| Random forest: expanded | 0.7186 | 0.8004 | 0.1828 | 0.5401 |

All results are preliminary **validation** scores. Lower Brier/log loss is better. The small gains from expanded features are not conclusive. A causal claim such as "taking dragons causes wins" is not supported by this observational predictive experiment.

See `Group27_ProgressReport.pdf` for the November 10 report, including both model families, and `MODEL_COMPARISON.md` for the detailed comparison and discussion questions. The tested forest does not clearly improve on logistic regression. Expanded forest features improve log loss conditionally, with uncertainty and multiple-comparison limitations described in the brief.

## Files

- `code/run_experiments.py`: full data checks, feature construction, fitting, evaluation and figures.
- `code/run_random_forest.py`: fixed forest comparisons using the existing logistic split and predictions.
- `code/verify_results.py`: saved-score, split and preprocessing checks for both model families.
- `results/model_family_comparison.csv` and `model_family_paired_comparisons.json`: direct comparisons and conditional uncertainty.
- `results/split_assignments.csv`: fixed match allocations, including the reserved test set.
- `results/data_audit.json`: dataset hash and structural checks.
- `results/experiment_config.json`: feature sets, settings, versions, convergence and split counts.
- `results/validation_metrics.csv` and `validation_predictions.csv`: full results and reproducible per-match validation outputs.
- `results/calibration_bins.csv`: probability-bin summaries and counts.
- `results/logistic_coefficients.csv`: fitted parameters and scaler statistics. Coefficients are associations conditional on other correlated inputs, not causal effects.
- `results/training_feature_summary.csv` and `training_feature_correlations.csv`: training-only exploratory summaries.
- `results/paired_validation_comparison.json`: uncertainty for the preselected expanded-versus-core contrast.
- `results/figures/`: report-ready calibration and confusion-matrix plots.
- `report/`: editable LaTeX report and bibliography using the instructor-provided style files.

## Dataset and scope

Ma, Y. L. (2020). *League of Legends Diamond Ranked Games (10 min)* (Version 1) [Dataset]. Kaggle. [Dataset page](https://www.kaggle.com/datasets/bobbyscience/league-of-legends-diamond-ranked-games-10-min).

The downloaded source metadata lists CC0; the uploader attributes collection to Riot's API. The report also cites Riot's documented allowance for personal research as the policy basis for this offline coursework study, without claiming project-specific approval or explicit model-training authorization. See `DATA.md` in the submission package or `docs/DATA.md` in the repository for the source links and limitations. The CSV does not identify dates, regions, patches or players. The uploader's rank description is not independently verified from the CSV. No claim of representativeness, chronological evaluation, independence across players or current-patch performance is made.

## Report and disclosure

The report includes the contribution statements confirmed by Savvy and dated future responsibilities for all three members. Contributions are not inferred from commit authorship. AI assistance covers source retrieval, planning, code generation, debugging, interpretation and report drafting. The session-recorded model is OpenAI Codex `gpt-6.1-sol`; hosted hardware, inference runtime and compute region are unavailable.

Using the syllabus's 4.32 g CO2/query convention, 22 visible user messages in this project chat give **95.04 g CO2**. This includes clarification responses, repository/API discussion and the three subsequent feedback/policy questions; it excludes system context and assistant/tool calls. Activity generating the separately supplied AI review is unobserved and outside this count. `report/ai_usage.json` records the scope and assumptions. This is an approximation, not measured inference emissions. See `report/build_report.ps1` to regenerate the tables from saved results and compile the PDF with the course's ACL style dependencies.
