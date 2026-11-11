"""Generate report tables directly from the saved experiment outputs."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT.parent / "results"
metrics = pd.read_csv(RESULTS / "all_validation_metrics.csv")
labels = {"majority": "Majority class", "constant_probability": "Training win rate",
          "gold_only": "Gold-only LR", "core": "Core LR", "core_objectives": "Core + objectives LR",
          "core_vision": "Core + vision LR", "core_objectives_vision": "Core + objectives + vision LR",
          "forest_core": "Core RF", "forest_expanded": "Core + objectives + vision RF"}
lines = [r"\begin{tabular}{lrrrrrrrr}", r"\toprule",
         r"Model & Inputs & Acc. & Prec. & Recall & F1 & AUC & Brier & Log loss \\", r"\midrule"]
for _, row in metrics.iterrows():
    values = [labels[row.model], str(int(row.n_features))]
    values += ["--" if pd.isna(row[key]) else f"{row[key]:.4f}" for key in
               ["accuracy", "precision_blue", "recall_blue", "f1_blue", "roc_auc", "brier", "log_loss"]]
    lines.append(" & ".join(values) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}"]
(ROOT / "results_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
summary = pd.read_csv(RESULTS / "training_feature_summary.csv").set_index("feature")
lines = [r"\begin{tabular}{lrr}", r"\toprule", r"Training feature & Mean & Std. dev. \\", r"\midrule"]
for key, label in [("gold", "Gold difference"), ("experience", "XP difference"),
                   ("kills", "Kill difference"), ("wards_placed", "Wards placed difference")]:
    row = summary.loc[key]
    lines.append(f"{label} & {row['mean']:.2f} & {row['std']:.2f}" + r" \\")
lines += [r"\bottomrule", r"\end{tabular}"]
(ROOT / "feature_summary_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Generated the nine-model results table and selected training statistics.")
