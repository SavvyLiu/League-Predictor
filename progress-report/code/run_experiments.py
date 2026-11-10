"""Reproduce the progress-report validation experiments; never evaluate the test set."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.calibration import calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, brier_score_loss, confusion_matrix, f1_score,
    log_loss, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
CORE = ["gold", "experience", "level", "lane_cs", "jungle_cs", "kills", "assists"]
OBJECTIVES = ["dragons", "heralds"]
VISION = ["wards_placed", "wards_destroyed"]
SOURCE_FIELDS = {
    "gold": "TotalGold", "experience": "TotalExperience", "level": "AvgLevel",
    "lane_cs": "TotalMinionsKilled", "jungle_cs": "TotalJungleMinionsKilled",
    "kills": "Kills", "assists": "Assists", "dragons": "Dragons",
    "heralds": "Heralds", "wards_placed": "WardsPlaced", "wards_destroyed": "WardsDestroyed",
}
EXPERIMENTS = {
    "gold_only": ["gold"],
    "core": CORE,
    "core_objectives": CORE + OBJECTIVES,
    "core_vision": CORE + VISION,
    "core_objectives_vision": CORE + OBJECTIVES + VISION,
}
LABELS = {
    "majority": "Majority class", "constant_probability": "Training win rate",
    "gold_only": "Gold only", "core": "Core",
    "core_objectives": "Core + objectives", "core_vision": "Core + vision",
    "core_objectives_vision": "Core + objectives + vision",
}


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_data(path: Path) -> tuple[pd.DataFrame, dict]:
    data = pd.read_csv(path)
    if data.isna().any().any() or data.gameId.duplicated().any():
        raise ValueError("Unexpected missing values or duplicate match IDs; review before training.")
    if set(data.blueWins.unique()) != {0, 1}:
        raise ValueError("Expected binary blueWins labels.")
    checks = {
        "blue_kills_equal_red_deaths": np.array_equal(data.blueKills, data.redDeaths),
        "red_kills_equal_blue_deaths": np.array_equal(data.redKills, data.blueDeaths),
        "gold_difference": np.allclose(data.blueGoldDiff, data.blueTotalGold - data.redTotalGold),
        "experience_difference": np.allclose(data.blueExperienceDiff, data.blueTotalExperience - data.redTotalExperience),
    }
    for side in ("blue", "red"):
        checks[f"{side}_gold_rate"] = np.allclose(data[f"{side}GoldPerMin"], data[f"{side}TotalGold"] / 10)
        checks[f"{side}_cs_rate"] = np.allclose(data[f"{side}CSPerMin"], data[f"{side}TotalMinionsKilled"] / 10)
    if not all(checks.values()):
        raise ValueError("A planned redundancy assumption failed; inspect the dataset.")
    audit = {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rows": len(data), "columns": len(data.columns), "source_predictors": len(data.columns) - 2,
        "bytes": path.stat().st_size,
        "labels": {str(k): int(v) for k, v in data.blueWins.value_counts().sort_index().items()},
        "missing_cells": int(data.isna().sum().sum()),
        "duplicate_ids": int(data.gameId.duplicated().sum()),
        "duplicate_predictor_rows": int(data.drop(columns=["gameId", "blueWins"]).duplicated().sum()),
        "constant_columns": [c for c in data if data[c].nunique() == 1],
        "redundancy_checks": {k: bool(v) for k, v in checks.items()},
        "excluded_rows": 0,
        "source_limitations": ["No dates, region, patch or player IDs", "Exact checkpoint provenance is not independently verifiable"],
    }
    return data, audit


def feature_frame(data: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({name: data["blue" + suffix] - data["red" + suffix]
                         for name, suffix in SOURCE_FIELDS.items()}, index=data.index)


def saved_splits(data: pd.DataFrame, results: Path) -> tuple[dict, dict]:
    path = results / "split_assignments.csv"
    if path.exists():
        saved = pd.read_csv(path)
        if len(saved) != len(data) or saved.gameId.duplicated().any():
            raise ValueError("Saved split does not match this dataset.")
        ordered = data[["gameId"]].merge(saved, on="gameId", how="left", validate="one_to_one")
        if ordered.split.isna().any() or set(ordered.split) != {"train", "validation", "test"}:
            raise ValueError("Invalid saved split.")
    else:
        train_idx, held_idx = train_test_split(data.index.to_numpy(), test_size=0.30,
                                             stratify=data.blueWins, random_state=SEED)
        valid_idx, test_idx = train_test_split(held_idx, test_size=0.50,
                                             stratify=data.loc[held_idx, "blueWins"], random_state=SEED)
        ordered = data[["gameId"]].copy()
        ordered["split"] = ""
        for name, idx in (("train", train_idx), ("validation", valid_idx), ("test", test_idx)):
            ordered.loc[idx, "split"] = name
        ordered.to_csv(path, index=False)
    indices = {name: np.flatnonzero(ordered.split.to_numpy() == name)
               for name in ("train", "validation", "test")}
    if sum(len(v) for v in indices.values()) != len(data):
        raise ValueError("Splits must cover each row exactly once.")
    # Label counts describe allocation; test predictions and test scores are never computed.
    summary = {name: {"n": len(idx), "blue_wins": int(data.iloc[idx].blueWins.sum()),
                      "red_wins": int((1 - data.iloc[idx].blueWins).sum())}
               for name, idx in indices.items()}
    return indices, summary


def metrics(y: np.ndarray, predicted: np.ndarray, probabilities: np.ndarray | None) -> dict:
    scores = {"accuracy": accuracy_score(y, predicted),
              "precision_blue": precision_score(y, predicted, zero_division=0),
              "recall_blue": recall_score(y, predicted, zero_division=0),
              "f1_blue": f1_score(y, predicted, zero_division=0)}
    if probabilities is not None:
        scores.update(roc_auc=roc_auc_score(y, probabilities),
                      brier=brier_score_loss(y, probabilities),
                      log_loss=log_loss(y, probabilities, labels=[0, 1]))
    else:
        scores.update(roc_auc=None, brier=None, log_loss=None)
    return scores


def paired_bootstrap(y: np.ndarray, base: np.ndarray, expanded: np.ndarray,
                     comparison: str = "core_objectives_vision minus core") -> dict:
    """Sampling intervals conditional on these fitted models, not training variability."""
    rng = np.random.default_rng(SEED)
    eps = np.finfo(float).eps
    def individual_loss(p):
        p = np.clip(p, eps, 1 - eps)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p))
    differences = {
        "accuracy": ((expanded >= 0.5) == y).astype(float) - ((base >= 0.5) == y).astype(float),
        "brier": (expanded - y) ** 2 - (base - y) ** 2,
        "log_loss": individual_loss(expanded) - individual_loss(base),
    }
    draws = {key: [] for key in differences}
    for _ in range(2000):
        idx = rng.integers(0, len(y), len(y))
        for key, values in differences.items():
            draws[key].append(float(values[idx].mean()))
    return {"comparison": comparison, "resamples": 2000, "seed": SEED,
            "scope": "Paired validation-row bootstrap conditional on fixed fitted models; does not include training/split variability or correct for multiple comparisons.",
            "differences": {key: {"estimate": float(values.mean()),
                                   "lower_95": float(np.quantile(draws[key], 0.025)),
                                   "upper_95": float(np.quantile(draws[key], 0.975))}
                            for key, values in differences.items()}}


def make_figures(y, predictions, probabilities, table, figures):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.dpi": 180})
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.8), constrained_layout=True)
    for name, color in (("gold_only", "#94a3b8"), ("core", "#2563eb"),
                        ("core_objectives_vision", "#c05621")):
        observed, predicted = calibration_curve(y, probabilities[name], n_bins=10, strategy="uniform")
        axes[0].plot(predicted, observed, "o-", markersize=3, lw=1.2, color=color, label=LABELS[name])
        axes[1].hist(probabilities[name], bins=np.linspace(0, 1, 11), histtype="step", lw=1.4,
                     color=color, label=LABELS[name])
    axes[0].plot([0, 1], [0, 1], "--", color="black", lw=0.8)
    axes[0].set(xlabel="Predicted blue-win probability", ylabel="Observed blue-win fraction",
                xlim=(0, 1), ylim=(0, 1), title="Validation reliability (10 bins)")
    axes[0].legend(fontsize=6.4, loc="upper left")
    axes[1].set(xlabel="Predicted blue-win probability", ylabel="Validation matches",
                title="Prediction distribution", xlim=(0, 1))
    fig.savefig(figures / "calibration.png")
    fig.savefig(figures / "calibration.pdf")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.7), constrained_layout=True)
    for ax, name in zip(axes, ("core", "core_objectives_vision")):
        cm = confusion_matrix(y, predictions[name], labels=[0, 1])
        ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.2)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=12)
        ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Red win", "Blue win"],
               yticklabels=["Red win", "Blue win"], xlabel="Predicted outcome",
               ylabel="True outcome", title=LABELS[name])
        ax.spines[:].set_visible(False)
    fig.savefig(figures / "confusion_matrices.png")
    fig.savefig(figures / "confusion_matrices.pdf")
    plt.close(fig)


def run(data_path: Path, results: Path) -> None:
    start = time.perf_counter()
    results.mkdir(parents=True, exist_ok=True)
    figures = results / "figures"
    figures.mkdir(exist_ok=True)
    data, audit = load_data(data_path)
    previous_audit = results / "data_audit.json"
    if previous_audit.exists() and json.loads(previous_audit.read_text())["sha256"] != audit["sha256"]:
        raise ValueError("Dataset hash changed. Use a separate results directory for changed data.")
    write_json(previous_audit, audit)
    idx, split_summary = saved_splits(data, results)
    x = feature_frame(data)
    train, valid = idx["train"], idx["validation"]
    x_train, x_valid = x.iloc[train], x.iloc[valid]
    y_train = data.blueWins.iloc[train].to_numpy()
    y_valid = data.blueWins.iloc[valid].to_numpy()
    training_stats = x_train.describe().T
    training_stats["outside_3sd_count"] = ((x_train - x_train.mean()).abs() > 3 * x_train.std()).sum()
    training_stats.to_csv(results / "training_feature_summary.csv", index_label="feature")
    x_train.corr().to_csv(results / "training_feature_correlations.csv", index_label="feature")
    rows, predictions, probabilities, diagnostics, coefficients = [], {}, {}, {}, []
    dummy_input = np.zeros((len(train), 1))
    majority = DummyClassifier(strategy="most_frequent").fit(dummy_input, y_train)
    pred = majority.predict(np.zeros((len(valid), 1)))
    predictions["majority"] = pred
    rows.append({"model": "majority", "n_features": 0, **metrics(y_valid, pred, None)})
    p_train = float(y_train.mean())
    p_constant = np.full(len(valid), p_train)
    pred_constant = (p_constant >= 0.5).astype(int)
    predictions["constant_probability"] = pred_constant
    probabilities["constant_probability"] = p_constant
    rows.append({"model": "constant_probability", "n_features": 0,
                 **metrics(y_valid, pred_constant, p_constant)})
    for name, columns in EXPERIMENTS.items():
        model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, solver="lbfgs",
                              penalty="l2", max_iter=2000, tol=1e-6, random_state=SEED))
        fit_start = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            model.fit(x_train[columns], y_train)
        convergence_warnings = [str(w.message) for w in caught if issubclass(w.category, ConvergenceWarning)]
        if convergence_warnings:
            raise RuntimeError("Optimization did not converge: " + name)
        scaler = model.named_steps["standardscaler"]
        if not np.allclose(scaler.mean_, x_train[columns].mean().to_numpy()):
            raise AssertionError("Scaler must use training rows only.")
        fitted = model.named_steps["logisticregression"]
        p = model.predict_proba(x_valid[columns])[:, list(model.classes_).index(1)]
        pred = (p >= 0.5).astype(int)
        probabilities[name], predictions[name] = p, pred
        rows.append({"model": name, "n_features": len(columns), **metrics(y_valid, pred, p)})
        diagnostics[name] = {"iterations": int(fitted.n_iter_[0]), "convergence_warnings": convergence_warnings,
                             "fit_seconds": time.perf_counter() - fit_start,
                             "training_log_loss": float(log_loss(y_train, model.predict_proba(x_train[columns])[:, 1])),
                             "intercept": float(fitted.intercept_[0])}
        for column, coef, mean, scale in zip(columns, fitted.coef_[0], scaler.mean_, scaler.scale_):
            coefficients.append({"model": name, "feature": column, "coefficient_standardized": float(coef),
                                 "training_mean": float(mean), "training_scale": float(scale)})
    table = pd.DataFrame(rows)
    table.to_csv(results / "validation_metrics.csv", index=False)
    prediction_frame = pd.DataFrame({"gameId": data.gameId.iloc[valid].to_numpy(), "blueWins": y_valid})
    for name, pred in predictions.items():
        prediction_frame[name + "_prediction"] = pred
        if name in probabilities:
            prediction_frame[name + "_probability"] = probabilities[name]
    prediction_frame.to_csv(results / "validation_predictions.csv", index=False)
    pd.DataFrame(coefficients).to_csv(results / "logistic_coefficients.csv", index=False)
    bin_rows = []
    for name, probs in probabilities.items():
        bin_id = np.minimum((probs * 10).astype(int), 9)
        for k in range(10):
            mask = bin_id == k
            if mask.any():
                bin_rows.append({"model": name, "bin_left": k / 10, "bin_right": (k + 1) / 10,
                                 "n": int(mask.sum()), "mean_probability": float(probs[mask].mean()),
                                 "observed_blue_win_rate": float(y_valid[mask].mean())})
    pd.DataFrame(bin_rows).to_csv(results / "calibration_bins.csv", index=False)
    write_json(results / "paired_validation_comparison.json",
               paired_bootstrap(y_valid, probabilities["core"], probabilities["core_objectives_vision"]))
    write_json(results / "confusion_matrices.json",
               {name: confusion_matrix(y_valid, pred, labels=[0, 1]).tolist() for name, pred in predictions.items()})
    make_figures(y_valid, predictions, probabilities, table, figures)
    config = {"seed": SEED, "split": split_summary, "dataset_sha256": audit["sha256"],
              "split_policy": "Stratified 70/15/15; saved assignments reused on rerun",
              "test_evaluated": False, "threshold": 0.5, "positive_class": "blueWins=1",
              "training_blue_win_rate": p_train, "experiments": EXPERIMENTS,
              "logistic": {"C": 1.0, "solver": "lbfgs", "penalty": "l2", "tol": 1e-6, "max_iter": 2000},
              "tuning": "None; fixed settings for this preliminary comparison",
              "preprocessing": "Blue-minus-red differences; training-fitted StandardScaler per model; no filtering/imputation/augmentation",
              "diagnostics": diagnostics,
              "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
                           "scikit-learn": sklearn.__version__, "scipy": scipy.__version__, "matplotlib": matplotlib.__version__},
              "elapsed_seconds": time.perf_counter() - start}
    write_json(results / "experiment_config.json", config)
    print(table.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print("\nSplit sizes:", {k: v["n"] for k, v in split_summary.items()})
    print("Test set evaluated: NO")
    print("Saved results:", results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "high_diamond_ranked_10min.csv")
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    run(args.data, args.results)
