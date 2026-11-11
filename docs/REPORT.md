# Report source and submission package

The November 10 report is `progress-report/Group27_ProgressReport.pdf`. Its editable source is `progress-report/report/main.tex`. It includes both forest rows, implementation details, feature statistics, two additional task-specific references, confirmed contributions, dated responsibilities and the AI-use estimate. The test set remains reserved.

The older logistic-only draft is retained locally as an archive and excluded from the final submission package. The separate model-comparison brief provides additional discussion detail.

## Build the main report

Use the ACL template supplied through the course's Avenue Final Project module. Copy its generic `acl.sty` and `acl_natbib.bst` files into `progress-report/report/`; those course-supplied dependencies and the handout archive remain local and are ignored by Git. The [ACL style repository](https://github.com/acl-org/acl-style-files) is also the upstream reference; the course version should be used for the submitted document.

With MiKTeX installed, on Windows:

```powershell
./progress-report/report/build_report.ps1
```

Alternatively, run pdfLaTeX, BibTeX, then pdfLaTeX twice from `progress-report/report/`. Additional standard LaTeX packages may need installation.

The helper requires the Python packages in `progress-report/requirements.txt`. It regenerates `results_table.tex` from `results/all_validation_metrics.csv` and `feature_summary_table.tex` from `results/training_feature_summary.csv`. Output is `output/pdf/Group27_ProgressReport.pdf`; copy it to `progress-report/Group27_ProgressReport.pdf` when publishing an updated build. Use `-PythonExecutable` to select a custom Python interpreter.

## Package and disclosure

The final `output/Group27_ProgressReport.zip` contains the PDF, experiment instructions, pinned dependencies, all three scripts, core CSV and source note, saved results, executed notebook and editable report source with the course style files. It excludes optional API/research tooling, credentials, fresh player data, build intermediates, previous draft PDFs and nested archives. It has not been submitted to Avenue by the assistant.

`report/ai_usage.json` records the 19-message count and 82.08 g CO2 approximation. Contribution statements use Savvy's factual confirmation rather than inferred commit ownership. No independent Riot/TA approval is claimed; the report documents the publisher's CC0 listing and the stated static-data coursework use.
