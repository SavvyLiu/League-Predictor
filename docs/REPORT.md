# Report source and current review status

The editable LaTeX source and bibliography are in `progress-report/report/`. The PDF there describes the earlier logistic-only milestone draft. The newest forest comparison is in `progress-report/MODEL_COMPARISON.md` and its one-page PDF.

The report still needs the new comparison integrated, factual contribution statements, complete AI-use/carbon disclosure and a final human review. It is not marked submission-ready.

## Build the main report

Use the ACL template supplied through the course's Avenue Final Project module. Copy its generic `acl.sty` and `acl_natbib.bst` files into `progress-report/report/`; those course-supplied dependencies and the handout archive remain local and are ignored by Git. The [ACL style repository](https://github.com/acl-org/acl-style-files) is also the upstream reference; the course version should be used for the submitted document.

With MiKTeX installed, on Windows:

```powershell
./progress-report/report/build_report.ps1
```

Alternatively, run pdfLaTeX, BibTeX, then pdfLaTeX twice from `progress-report/report/`. Additional standard LaTeX packages may need installation.

The model results table is currently checked in as `results_table.tex`. When revising the report to include new runs, update both its table and the surrounding explanations to match the measured CSV outputs. The supplied initial table contains the earlier logistic comparisons only.
