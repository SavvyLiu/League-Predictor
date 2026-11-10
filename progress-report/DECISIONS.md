# Experiment decisions and review status

Implemented November 10, 2026, after the November 9 planning/source review.

**Follow-up comparison:** at Savvy's request, two fixed random forests were fitted to the same core/expanded inputs and saved split. Core accuracy is 71.79%; expanded accuracy is 71.86%. No clear advantage over matched logistic models was found. See `MODEL_COMPARISON.md` for full results, uncertainty and questions for the TA/team. No more data will be collected or scope broadened before that discussion. The report PDF remains the earlier logistic-only draft until revised after feedback.

1. **Dataset:** retain the already checked original Kaggle CSV. The separate ten-match API pilot is collection evidence only. No new API collection was attempted.
2. **Representation:** compute blue-minus-red differences. Exclude IDs and exact redundancy. Seven core inputs; objectives and vision each add two. This trades away absolute-state information for a clear initial comparison.
3. **Data quality:** retain all rows. Extreme vision values remain unverified; arbitrary three-sigma deletion could remove meaningful cases. Training-only summaries flag them for later investigation.
4. **Evaluation:** save stratified seed-42 train/validation/test allocations (6,915/1,482/1,482). Do not evaluate test performance during this milestone. Preserve the same split for every model.
5. **Model:** use scikit-learn L2 logistic regression, `C=1`, L-BFGS, tolerance `1e-6`, maximum 2,000 iterations. This is a deliberate simplification of the proposal's broader model list and SGD suggestion. All five fits converged.
6. **Comparison:** use majority and training-win-probability baselines, then gold-only, core, core+objectives, core+vision, and core+both. Keep settings fixed rather than searching for a favorable validation result.
7. **Probability evaluation:** report Brier/log loss and a reliability diagram as well as accuracy/F1/AUC. No post-hoc probability calibration has been fitted.
8. **Interpretation:** objectives yield small improvements on this split; vision alone leaves accuracy unchanged. Combined minus core accuracy is +0.20 percentage points; paired-bootstrap intervals include zero. This does not establish a reliable benefit, a causal objective effect, or that vision is unimportant.
9. **Verification:** the walkthrough ran successfully. Independent verification reconstructs saved probabilities from coefficients, checks training-only scaler values and split isolation, and recalculates accuracy/Brier/log loss from saved predictions.
10. **Report status:** review draft. Individual contributions and the complete AI-use/emissions disclosure are still pending factual confirmation. No contribution is inferred from a commit or use of a single machine. No upload or submission has occurred.

## Remaining before submission

- Read and verify the report in your own words, especially the optimization/evaluation explanations.
- Confirm actual contributions for all three registered members.
- Complete the model/usage count/assumptions and emissions estimate for AI assistance. Distinguish remote model inference from local experiment runtime.
- Add any newer TA feedback or data-use evidence if available; otherwise retain the accurately stated uncertainty.
- Remove the review-draft label only after the incomplete sections are resolved; rebuild and inspect the PDF.
- Zip the report, code and selected CSV once, upload to Avenue, then download and check the uploaded archive.
