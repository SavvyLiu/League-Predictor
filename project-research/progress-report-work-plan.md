# Group 27 progress report work plan

Prepared November 9, 2026. All times are America/Toronto (EST).

**Execution update, November 10:** data checks and all planned logistic/baseline experiments have now run successfully in `C:/Code/4al3/progress-report/`. An executed walkthrough, saved validation results and a report review draft are being prepared there. Core accuracy is 71.93%; objectives alone 72.27%; objectives plus vision 72.13%. No test performance has been evaluated. See `progress-report/DECISIONS.md` for current choices and the remaining factual confirmations. The dated schedule below is the original plan, not a claim that its November 9 targets were completed then.

**Official deadline: Tuesday, November 10, 2026, 11:59:59 p.m. EST.** Target upload: 9 p.m. on November 10, leaving time to download and check the submitted archive.

Project: Early-Game Win Prediction in League of Legends Using Match Statistics. Team: Savvy Liu, Peter Li, Krish Panchal. TA: Hongyi Zhang.

**Updated work arrangement:** Savvy will complete all remaining progress-report work. The schedule below is sequential and does not depend on teammate handoffs. This does not change the group membership or imply that Savvy completed other members' earlier work. Contribution statements must describe actual work. The plan is based on the current local project files, the official progress-report handout and template, Avenue assignment information and proposal feedback, and relevant Teams posts. Reuse any existing teammate work already available without making it a dependency. See [source notes](progress-report-source-notes.md).

## What has to be submitted

- A PDF using the supplied ACL-style LaTeX template, with about **four pages of content excluding the space occupied by graphs and tables**. The handout does not explicitly exempt references from that count. Do not reuse the proposal's Times New Roman 12 / 1.5-spacing rules.
- At least **five cited references** and every report item in the table below.
- Code and the dataset, bundled with the PDF into **one archive** for Avenue. The selected CSV is 1,446,502 bytes, well below 50 MB, so include it. The over-50-MB data-link exception is unnecessary for this dataset.
- A trained model actually run on the project data and a simple baseline. High performance and beating published results are not requirements for this milestone.
- TA feedback and a concrete plan for the remaining project. **No explicit or in-person approval is required.** Feedback can have been received at any point before the deadline; existing feedback is usable if accurately identified and discussed.
- Actual contributions from all three members. Include AI-use and carbon-footprint disclosure under the syllabus policy; the report handout does not specify its placement, so put it visibly in the PDF and give additional details in the README if needed.

The official source files are in `C:/Code/4al3/Project Progress Report/`: the instructions PDF and `Proposal LaTeX/main.tex`, `acl.sty`, `acl_natbib.bst`, and `custom.bib`.

## Requirements and ownership

| Weight | Required content | Owner of remaining work | Evidence/output |
| --- | --- | --- | --- |
| 15% | Dataset properties and preprocessing actually performed | Savvy | Dataset summary, source citation, data checks, exact cleaning choices, included CSV |
| 10% | Brief introduction, related work, at least five references | Savvy | Concise motivation, five relevant research references, bibliography |
| 10% | Model inputs, feature engineering/selection/augmentation | Savvy | Exact input-column list and representation; dimensions per experiment |
| 20% | Implemented and run model; baseline; loss and optimization | Savvy | Runnable notebook/script, saved settings and results, description matching the code |
| 20% | Splits/CV, metrics, preliminary results | Savvy | Fixed split IDs, validation metric table, appropriate figures, leakage controls |
| 20% | TA feedback, reflection, next steps informed by progress | Savvy | Feedback-to-action table, actual difficulties, dated remaining-work plan |
| 5% | Each member's contributions | Savvy assembles factual statements | A few sentences per person reflecting actual contributions; no invented or equalized credit |

## Current evidence and gaps

**Ready to reuse:** the proposal; dataset provenance investigation; the downloaded original Kaggle CSV; alternative-dataset audits; and a ten-match Riot API feasibility pilot. A fresh November 9 CSV check confirmed 9,879 unique matches, 40 columns including ID and label, 4,930 blue wins / 4,949 losses, zero missing cells, zero duplicate IDs, and no constant source columns. The saved check is `findings/progress-report-readiness-2026-11-09.json`.

**Not found in the local project materials:** a trained League model, saved train/validation/test assignments, project evaluation scores, or a draft progress report. Homework 2 SVM results concern a separate task and cannot serve as League project results. Check teammate files before treating these as unfinished team work.

**Proposal feedback:** Avenue reports **18.65/20**. Hongyi asked for a task-specific reason for choosing SVMs and neural networks, and flagged a nested ZIP. Fix these directly: explain the purpose of each model actually retained, describe deferred models as future work, and submit a single archive containing ordinary folders/files.

**Important distinction:** the ten-match API pilot demonstrates collection and feature extraction. It is not a trained-model experiment or evidence of prediction quality. The original dataset's missing dates/region/patches limit generalization and prevent a verified chronological split. The earlier training-permission question remains unresolved in the records reviewed; report its actual status and any newer team evidence without claiming clearance from successful API access.

## Minimum implementation for this milestone

Use the original 9,879-match Kaggle dataset for the core experiment, unless the team has already made and implemented a better-supported change. Keep fresh API collection, champion/item interactions, multiple time checkpoints, an application interface, and a full neural-network comparison for later work. For the solo workload, target majority/constant-probability baselines plus gold-only, core and expanded-feature logistic regression. A random forest is optional only after the report is complete; SVMs and neural networks can remain justified future work.

1. **Freeze the task and data.** Predict `blueWins` from ten-minute statistics. Keep `gameId` only for identifying rows. Record the CSV hash and the exact input columns. Confirm the team is using one dataset and representation throughout the report.
2. **Create and save one stratified 70/15/15 train/validation/test split.** Use a recorded seed, such as 42. Fit learned preprocessing on training rows only. Use validation results in the progress report and retain the test set for the final project. If the team already has legitimate test results, document that fact and avoid repeated model selection against them.
3. **Run the simple baseline.** Fit majority-class predictions from the training labels for classification metrics. For probability metrics, use the constant training-set blue-win rate as a separate probability baseline. Do not choose either baseline from validation/test labels.
4. **Run two useful logistic comparisons.** Gold-difference-only logistic regression establishes what one obvious signal can do. Logistic regression on a compact economy/experience/farming/combat representation is the main initial learned model. Record the actual regularization, solver, stopping settings, and whether it converged. Explain binary cross-entropy and the optimization actually used; do not describe mini-batch SGD if the implementation uses a different solver.
5. **Run one feature ablation if time permits.** Hold the model and row split fixed, then add objectives and vision to the same core feature set. This addresses the team's proposed experiment without building a new collection pipeline. Do not add a nonlinear model until the report and required submission files are complete.
6. **Save evidence.** A machine-readable validation table, exact experiment settings, a confusion matrix for the main model, and a reliability/calibration plot are useful. Report accuracy, precision/recall/F1 and ROC-AUC for classification, plus Brier score and log loss for probability quality. For a class-only baseline, leave unavailable probability metrics blank or use the explicitly named constant-probability baseline.
7. **Write observations after running.** Explain what changed with extra features, where errors occur, and limitations. A small or negative improvement is a valid preliminary finding. Add further calibration/tuning to future work unless it has actually been run with an appropriate training-only fitting procedure.

### Feature decisions to settle before training

Start with blue-minus-red differences for gold, XP, average level, lane CS, jungle CS, kills, and assists (seven core inputs). Add dragon, Herald, wards-placed, and wards-destroyed differences for the expanded experiment (eleven inputs). This is a proposed starting point, not an already tested selection. Preserve any different existing team implementation and document its actual columns.

- Omit a deaths difference when kills difference is present: blue kills equal red deaths and vice versa in this CSV.
- Avoid retaining both sides plus their exact difference without explaining the redundancy. The proposal's 38 source predictors and the earlier 36 engineered candidates describe different representations.
- At a fixed ten-minute checkpoint, gold/minute and CS/minute reproduce totals divided by ten in the inspected blue-side columns. Confirm equivalent red-side relations before removing their redundant rates.
- Do not claim Herald features are all zero: the current CSV contains 1,857 blue and 1,581 red Herald captures. There are no constant source columns.
- Inspect extreme values; do not automatically delete every row outside three standard deviations. Legitimate snowball matches may be extreme, and exclusions require justification. Fit any learned thresholds using training data only.
- Standardize continuous inputs for logistic/SVM models within the fitted pipeline. A tree model does not need scaling. Counts and binary flags should be described accurately rather than calling all inputs ratio-type features.

## Schedule through the deadline

These are proposed internal targets for Savvy, not additional course deadlines. Work through the sequence in order; adjust start times around availability and keep the upload buffer. Reuse the proposal, source notes and checked dataset rather than restarting research.

| When (EST) | Work | Finished when |
| --- | --- | --- |
| Nov 9, first 30 minutes | Freeze dataset, core/expanded features, seed and split; inspect any existing implementation already available | One experiment specification |
| Nov 9, next 2-3 hours | Build one reproducible pipeline and run majority, constant-probability, gold-only and core logistic baselines | Saved split identifiers, settings and measured validation results |
| Nov 9, next 1-2 hours | Add objectives/vision comparison; export one metrics table, confusion matrix and calibration plot | Results ready to explain in the report |
| Nov 9, next 30 minutes | Outline the report in the supplied template and map existing TA feedback to actions | All required sections present; no dependency on a new TA reply |
| Nov 9, remainder of workday; target 9 p.m. | Write the full draft using existing proposal/source notes, then add actual results, feedback/plans and contributions | Complete first draft with five cited references |
| Nov 10, by noon | Re-run from a clean start; reconcile code, features, numbers, and prose | Reproducible results and internally consistent claims |
| Nov 10, by 4 p.m. | Assemble and inspect PDF; check reference count, four-page text target, figures, disclosure, and contributions | Reviewed submission-ready PDF |
| Nov 10, by 7 p.m. | Package report/code/data/README; extract and test the archive | One working archive with no nested ZIPs or unrelated datasets |
| Nov 10, target 9 p.m. | Savvy uploads, downloads the uploaded archive and checks it | Correct files verified in the Avenue submission before 11:59:59 p.m. |

Budget approximately **12-16 focused hours total** if starting implementation from scratch: 0.5 hour to settle scope, 2-3 hours for the pipeline/baselines, 1-2 hours for the feature comparison and figures, 5-6 hours for the report/references, and 2-4 hours for reproduction, revision and packaging. These are estimates, not measured runtimes. If behind, cut random forest, broad tuning and additional plots first. Preserve a model actually run, a baseline, every required report section and time to inspect the submitted archive.

## Report structure and space budget

Follow the supplied section order. Aim for roughly 4-4.5 pages of prose overall, with additional space for figures and tables; check the compiled document rather than enforcing these estimates rigidly.

| Section | Approximate prose | What to emphasize |
| --- | --- | --- |
| Introduction | 0.3 page | Ten-minute prediction task, motivation, scope |
| Related Work | 0.4 page | Five useful research sources and how they guide this experiment |
| Dataset | 0.7 page | Source, rows/labels, completed preprocessing, limitations |
| Features | 0.35 page | Exact representation and ablation inputs |
| Implementation | 0.9 page | Actual trained model, baseline, loss/optimization, choices |
| Results and Evaluation | 0.55 page | Split, leakage controls, metrics, measured findings |
| Feedback and Plans | 0.6 page | Feedback addressed and specific work remaining |
| Team Contributions | 0.15 page | Work actually completed by each person |

Remove the template's demonstration text, placeholder figures, dummy references and `Template Notes` section. Do not remove the real Team Contributions section. Use Group 27 and the three actual names/MacIDs.

## Packaging checklist

Suggested contents of the eventual submission archive (these are planned outputs, not files already produced here):

```text
Group27_ProgressReport.pdf
README.md
requirements.txt
code/                    # notebook or scripts that reproduce reported results
data/high_diamond_ranked_10min.csv
results/                 # reported tables, figures, split identifiers/settings
```

- Document exact run instructions, dataset citation, split seed and file, and which results are preliminary validation results.
- Include the selected CSV, not the multi-dataset research archive or the instructor's source ZIP.
- Keep API keys and raw pilot files with player identifiers out of the submission; the core Kaggle experiment does not require them.
- Make disclosure describe actual AI assistance, including this research/planning session. Use the syllabus estimation method and describe assumptions; do not invent provider hardware or compute location. Ask all members for their own usage records.
- Keep the existing group names. State that Savvy completed the remaining implementation/report work if that is what occurred, and describe Peter's and Krish's actual earlier or current contributions separately. Do not reuse the old proposed division as evidence of completed work. If details are uncertain, verify them without making the whole build depend on a handoff.
- Download the uploaded archive immediately and verify the PDF, code and CSV are the intended versions.

## Remaining work after this milestone

The course's current Dates module lists the final project for December 10. Proposed internal targets: by November 17, finish justified SVM/forest comparisons and settle feature representation; by November 24, assess calibration and a limited neural network if warranted; by December 1, finish ablations, error analysis and limitations; by December 7, freeze model selection and evaluate on the held-out test set once; December 8-10, complete the final report and any modest historical-match demonstration. Adjust this sequence to the final-report handout when released. Use fresh Riot collection or champion/item context only if the core work, data-use status and time support it.
