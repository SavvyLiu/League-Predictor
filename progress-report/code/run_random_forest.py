"""Compare fixed random forests with existing logistic runs on identical validation matches."""

import hashlib
import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, log_loss

from run_experiments import CORE, OBJECTIVES, VISION, SEED, feature_frame, load_data, metrics, paired_bootstrap, write_json

ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = dict(n_estimators=500, criterion="gini", max_depth=8, min_samples_leaf=10,
                  min_samples_split=2, max_features="sqrt", bootstrap=True,
                  random_state=SEED, n_jobs=-1, class_weight=None)
FOREST_INPUTS = {"forest_core": CORE, "forest_expanded": CORE + OBJECTIVES + VISION}


def run(root=ROOT):
    results = root / "results"
    data_path = root / "data" / "high_diamond_ranked_10min.csv"
    data, audit = load_data(data_path)
    original = json.loads((results / "experiment_config.json").read_text())
    if audit["sha256"] != original["dataset_sha256"]:
        raise ValueError("Data differ from the existing logistic experiment.")
    split_path = results / "split_assignments.csv"
    split = pd.read_csv(split_path)
    allocation = data[["gameId"]].merge(split, on="gameId", how="left", validate="one_to_one")
    if allocation.split.isna().any() or set(allocation.split) != {"train", "validation", "test"}:
        raise ValueError("Invalid saved split.")
    train = np.flatnonzero(allocation.split.to_numpy() == "train")
    valid = np.flatnonzero(allocation.split.to_numpy() == "validation")
    features = feature_frame(data)
    y_train = data.blueWins.iloc[train].to_numpy()
    y_valid = data.blueWins.iloc[valid].to_numpy()
    logistic = pd.read_csv(results / "validation_predictions.csv")
    if not np.array_equal(logistic.gameId, data.gameId.iloc[valid].to_numpy()):
        raise ValueError("Validation match order differs from the saved logistic predictions.")
    if not np.array_equal(logistic.blueWins, y_valid):
        raise ValueError("Validation labels differ from the original experiment.")
    predictions = logistic[["gameId", "blueWins"]].copy()
    rows, diagnostics, probabilities = [], {}, {}
    importances = []
    for name, columns in FOREST_INPUTS.items():
        start = time.perf_counter()
        forest = RandomForestClassifier(**PARAMETERS)
        # Trees split on thresholds; no fitted scaling or other learned preprocessing is used.
        forest.fit(features.iloc[train][columns], y_train)
        probability = forest.predict_proba(features.iloc[valid][columns])[:, list(forest.classes_).index(1)]
        predicted = (probability >= 0.5).astype(int)
        probabilities[name] = probability
        predictions[name + "_probability"] = probability
        predictions[name + "_prediction"] = predicted
        rows.append({"model": name, "n_features": len(columns), **metrics(y_valid, predicted, probability)})
        diagnostics[name] = {
            "fit_and_predict_seconds": time.perf_counter() - start,
            "training_accuracy": float(forest.score(features.iloc[train][columns], y_train)),
            "training_log_loss": float(log_loss(y_train, forest.predict_proba(features.iloc[train][columns])[:, 1])),
            "confusion_matrix": confusion_matrix(y_valid, predicted, labels=[0, 1]).tolist(),
            "tree_depth_min": int(min(t.tree_.max_depth for t in forest.estimators_)),
            "tree_depth_max": int(max(t.tree_.max_depth for t in forest.estimators_)),
            "features_considered_per_split": int(forest.estimators_[0].max_features_),
        }
        for column, importance in zip(columns, forest.feature_importances_):
            importances.append({"model": name, "feature": column, "mean_impurity_decrease": float(importance)})
    forest_metrics = pd.DataFrame(rows)
    forest_metrics.to_csv(results / "random_forest_metrics.csv", index=False)
    predictions.to_csv(results / "random_forest_validation_predictions.csv", index=False)
    pd.DataFrame(importances).to_csv(results / "random_forest_impurity_importances.csv", index=False)
    original_metrics = pd.read_csv(results / "validation_metrics.csv")
    combined = pd.concat([original_metrics, forest_metrics], ignore_index=True)
    combined.to_csv(results / "all_validation_metrics.csv", index=False)
    comparison = combined[combined.model.isin(["core", "core_objectives_vision", "forest_core", "forest_expanded"])]
    comparison.to_csv(results / "model_family_comparison.csv", index=False)
    contrasts = {
        "forest_core_minus_logistic_core": (logistic.core_probability.to_numpy(), probabilities["forest_core"]),
        "forest_expanded_minus_logistic_expanded": (logistic.core_objectives_vision_probability.to_numpy(), probabilities["forest_expanded"]),
        "forest_expanded_minus_forest_core": (probabilities["forest_core"], probabilities["forest_expanded"]),
    }
    write_json(results / "model_family_paired_comparisons.json",
               {name: paired_bootstrap(y_valid, base, extra, name) for name, (base, extra) in contrasts.items()})
    write_json(results / "random_forest_config.json", {
        "dataset_sha256": audit["sha256"],
        "split_file_sha256": hashlib.sha256(split_path.read_bytes()).hexdigest(),
        "n_train": len(train), "n_validation": len(valid), "test_evaluated": False,
        "parameters": PARAMETERS, "features": FOREST_INPUTS, "threshold": 0.5,
        "tuning": "No parameter search; one fixed forest configuration chosen before viewing forest scores",
        "preprocessing": "Same blue-minus-red differences; no scaling, filtering or augmentation",
        "learning": "Bootstrap decision trees use greedy Gini-impurity reduction; probability is the mean of tree leaf class proportions",
        "diagnostics": diagnostics, "scikit-learn_version": sklearn.__version__,
        "importance_caution": "Impurity importance can favor high-cardinality variables and share credit among correlated inputs; not causal or held-out importance.",
    })
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.8), constrained_layout=True)
    plt.rcParams.update({"font.size": 9})
    for ax, title, lr_name, rf_name in [
        (axes[0], "Core features", "core", "forest_core"),
        (axes[1], "Core + objectives + vision", "core_objectives_vision", "forest_expanded")]:
        for label, probs, color in [("Logistic regression", logistic[lr_name + "_probability"].to_numpy(), "#2563eb"),
                                    ("Random forest", probabilities[rf_name], "#c05621")]:
            observed, predicted = calibration_curve(y_valid, probs, n_bins=10, strategy="uniform")
            ax.plot(predicted, observed, "o-", color=color, lw=1.2, markersize=3, label=label)
        ax.plot([0, 1], [0, 1], "k--", lw=0.8)
        ax.set(title=title, xlabel="Predicted blue-win probability", ylabel="Observed blue-win fraction", xlim=(0, 1), ylim=(0, 1))
        ax.legend(fontsize=7)
        ax.spines[["top", "right"]].set_visible(False)
    for extension in ("png", "pdf"):
        fig.savefig(results / "figures" / ("model_family_calibration." + extension), dpi=180)
    plt.close(fig)
    print(comparison.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print("\nFixed forest configuration:", PARAMETERS)
    print("Test set evaluated: NO")


if __name__ == "__main__":
    run()
