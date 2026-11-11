# Group 27: logistic regression and random-forest comparison

November 10, 2026. Prepared for discussion with Hongyi Zhang and the team. These are preliminary validation results, not final test results.

## Question

Do nonlinear interactions improve ten-minute League of Legends win prediction beyond our initial logistic regression? Do objectives and vision help under both model families?

## Controlled setup

- Same original Kaggle CSV: 9,879 matches; existing stratified split: 6,915 train, 1,482 validation, 1,482 reserved test. Match assignments and dataset hash were unchanged.
- Same feature representations: seven blue-minus-red core differences (gold, XP, average level, lane CS, jungle CS, kills, assists); expanded set adds dragon, Herald, wards-placed and wards-destroyed differences (eleven features).
- Logistic regression: training-fitted standardization, L2 penalty, C=1, L-BFGS. Forest: raw differences, with no scaling required for threshold splits.
- Forest settings fixed before inspecting its scores: **500 trees, maximum depth 8, minimum 10 bootstrap samples per leaf, square-root feature subsampling, bootstrap sampling, Gini split criterion, seed 42**. This moderately constrains tree complexity and avoids tiny leaves. It is one reasonable initial configuration, not a tuned optimum or an exhaustive test of nonlinear models.
- A forest averages the leaf class proportions from its trees to produce win probabilities. It learns threshold rules and feature interactions using greedy Gini-impurity reduction; it does not optimize the logistic-regression cross-entropy objective.
- No hyperparameter search, cross-validation, post-hoc calibration, extra data collection or test-set performance evaluation was performed.

## Results on the same validation matches

| Model | Features | Accuracy | ROC-AUC | Brier (lower better) | Log loss (lower better) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Majority / training-rate baseline | 0 | 50.07% | 0.5000* | 0.25000* | 0.69315* |
| Logistic regression | Core: 7 | 71.93% | 0.79846 | 0.18362 | 0.54331 |
| Random forest | Core: 7 | 71.79% | 0.79647 | 0.18437 | 0.54571 |
| Logistic regression | Expanded: 11 | 72.13% | 0.80038 | 0.18285 | 0.53990 |
| Random forest | Expanded: 11 | 71.86% | 0.80037 | 0.18278 | 0.54012 |

*Baseline probability metrics use the constant training blue-win frequency (0.49906), rather than hard majority-class probabilities. The earlier gold-only logistic baseline achieved 71.05% accuracy. The earlier core-plus-objectives logistic configuration achieved 72.27%; it remains the highest observed accuracy among these initial runs, but is not a proven final winner.

## Interpretation

1. **The tested forest does not clearly outperform logistic regression.** On core inputs it makes two fewer correct predictions; on expanded inputs, four fewer. Expanded-model AUC and probability scores are almost the same across families. This is consistent with much of the usable signal being captured by the current linear model, but does not establish that nonlinear modeling cannot help after tuning or with richer inputs.
2. **Feature additions help the forest's probability predictions more than its hard decisions.** Expanded-minus-core forest log loss is -0.00560; accuracy improves by only one correct match. That is why evaluating probabilities alongside accuracy matters. This comparison adds objectives and vision together, so it does not isolate their individual contributions within the forest.
3. **Small differences need caution.** Paired 2,000-resample validation-row bootstrap intervals are listed below. Model-family differences include zero. The forest feature-extension log-loss interval excludes zero conditionally, but it is exploratory, unadjusted for multiple comparisons and does not capture training/split variability or player dependence.

| Comparison (second model minus reference) | Accuracy difference, percentage points [95% interval] | Log-loss difference [95% interval] |
| --- | --- | --- |
| Forest core minus logistic core | -0.13 [-1.08, +0.74] | +0.00240 [-0.00235, +0.00705] |
| Forest expanded minus logistic expanded | -0.27 [-1.28, +0.74] | +0.00022 [-0.00509, +0.00585] |
| Forest expanded minus forest core | +0.07 [-1.01, +1.15] | -0.00560 [-0.01072, -0.00075] |

The forest training accuracies are 75.82% (core) and 76.92% (expanded), versus approximately 71.8% on validation. The higher training performance suggests some fitting advantage does not transfer to held-out matches. It does not by itself establish whether the chosen depth/leaf settings are optimal.

## What to discuss with the TA/team

- Is a controlled linear/nonlinear comparison, feature ablation, probability evaluation and error analysis an appropriate scope for the **progress report**, with broader comparisons reserved for the final project?
- Should the next priority be training-only cross-validation and a modest regularization/depth/leaf-size search, or richer data/features?
- The original CSV lacks dates, patches, region and player IDs, and contains unusual vision values. Which limitations are acceptable for the core historical-data task, and which would justify switching to documented API collection?
- Is the previous model-training data-use question sufficiently addressed, or is further evidence needed?

More data is not yet shown to be necessary by these scores alone. A useful follow-up would be a training-only learning-curve experiment before deciding whether to collect more rows. If richer champion/item context is desired, it requires a new compatible dataset; it cannot be added by simply joining the ten-match feasibility pilot to the original Kaggle rows.

## Reproduce and review

Run `python code/run_experiments.py`, then `python code/run_random_forest.py`, then `python code/verify_results.py` from the experiment package. The new results are in `results/model_family_comparison.csv`, `random_forest_config.json`, `random_forest_validation_predictions.csv` and `model_family_paired_comparisons.json`. The comparison reliability diagram is in `results/figures/model_family_calibration.png`.

The November 10 `Group27_ProgressReport.pdf` integrates these results and includes confirmed contribution statements, dated responsibilities and the scoped AI-use estimate. This brief retains more comparison detail and questions for the TA/team. No report has been submitted by the assistant.

Method references: [Breiman (2001), Random Forests](https://www.stat.berkeley.edu/users/breiman/randomforest2001.pdf); [scikit-learn 1.6.1 forest documentation](https://scikit-learn.org/1.6/modules/generated/sklearn.ensemble.RandomForestClassifier.html).
