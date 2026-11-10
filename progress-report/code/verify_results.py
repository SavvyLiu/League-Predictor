"""Independently check saved predictions, split isolation and numerical summaries."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    results = root / "results"
    data_path = root / "data" / "high_diamond_ranked_10min.csv"
    data = pd.read_csv(data_path).set_index("gameId")
    split = pd.read_csv(results / "split_assignments.csv").set_index("gameId")
    predictions = pd.read_csv(results / "validation_predictions.csv").set_index("gameId")
    scores = pd.read_csv(results / "validation_metrics.csv").set_index("model")
    coefficients = pd.read_csv(results / "logistic_coefficients.csv")
    config = json.loads((results / "experiment_config.json").read_text())
    assert hashlib.sha256(data_path.read_bytes()).hexdigest() == config["dataset_sha256"]
    assert split.index.is_unique and set(split.index) == set(data.index)
    assert predictions.index.is_unique
    assert set(predictions.index) == set(split.index[split.split == "validation"])
    assert not set(predictions.index) & set(split.index[split.split == "test"])
    assert np.array_equal(predictions.blueWins, data.loc[predictions.index, "blueWins"])
    assert config["test_evaluated"] is False
    train = data.loc[split.index[split.split == "train"]]
    valid = data.loc[predictions.index]
    # Independent mapping/reconstruction, without importing the training implementation.
    suffixes = {"gold": "TotalGold", "experience": "TotalExperience", "level": "AvgLevel",
                "lane_cs": "TotalMinionsKilled", "jungle_cs": "TotalJungleMinionsKilled",
                "kills": "Kills", "assists": "Assists", "dragons": "Dragons",
                "heralds": "Heralds", "wards_placed": "WardsPlaced", "wards_destroyed": "WardsDestroyed"}
    y = predictions.blueWins.to_numpy()
    for name, columns in config["experiments"].items():
        saved = coefficients[coefficients.model == name].set_index("feature").loc[columns]
        train_x = np.column_stack([(train["blue" + suffixes[c]] - train["red" + suffixes[c]]).to_numpy()
                                   for c in columns])
        valid_x = np.column_stack([(valid["blue" + suffixes[c]] - valid["red" + suffixes[c]]).to_numpy()
                                   for c in columns])
        assert np.allclose(saved.training_mean, train_x.mean(axis=0))
        assert np.allclose(saved.training_scale, train_x.std(axis=0, ddof=0))
        standardized = (valid_x - saved.training_mean.to_numpy()) / saved.training_scale.to_numpy()
        reconstructed = expit(standardized @ saved.coefficient_standardized.to_numpy()
                              + config["diagnostics"][name]["intercept"])
        assert np.allclose(reconstructed, predictions[name + "_probability"], atol=1e-12)
    for name in scores.index:
        hard = predictions[name + "_prediction"].to_numpy()
        assert np.isclose(np.mean(hard == y), scores.loc[name, "accuracy"])
        if name != "majority":
            p = predictions[name + "_probability"].to_numpy()
            assert np.all((p >= 0) & (p <= 1))
            assert np.array_equal(hard, (p >= 0.5).astype(int))
            assert np.isclose(np.mean((p - y) ** 2), scores.loc[name, "brier"])
            loss = -np.mean(y * np.log(p) + (1 - y) * np.log1p(-p))
            assert np.isclose(loss, scores.loc[name, "log_loss"])
    assert np.isclose(predictions.constant_probability_probability.iloc[0], train.blueWins.mean())
    assert predictions.majority_prediction.nunique() == 1
    assert predictions.majority_prediction.iloc[0] == train.blueWins.mode().iloc[0]
    print("PASS: dataset identity; disjoint saved split; validation-only predictions; training-only scaler;")
    print("      independent sigmoid reconstruction; reported accuracy, Brier and log loss; baseline values.")
    forest_path = results / "random_forest_validation_predictions.csv"
    if forest_path.exists():
        forest = pd.read_csv(forest_path).set_index("gameId")
        forest_scores = pd.read_csv(results / "random_forest_metrics.csv").set_index("model")
        forest_config = json.loads((results / "random_forest_config.json").read_text())
        assert forest.index.is_unique and forest.index.equals(predictions.index)
        assert np.array_equal(forest.blueWins, y)
        assert forest_config["dataset_sha256"] == config["dataset_sha256"]
        assert forest_config["test_evaluated"] is False
        assert forest_config["split_file_sha256"] == hashlib.sha256((results / "split_assignments.csv").read_bytes()).hexdigest()
        for name in forest_scores.index:
            p = forest[name + "_probability"].to_numpy()
            hard = forest[name + "_prediction"].to_numpy()
            assert np.all((p >= 0) & (p <= 1))
            assert np.array_equal(hard, (p >= 0.5).astype(int))
            assert np.isclose(np.mean(hard == y), forest_scores.loc[name, "accuracy"])
            assert np.isclose(np.mean((p - y) ** 2), forest_scores.loc[name, "brier"])
            assert np.isclose(-np.mean(y * np.log(p) + (1 - y) * np.log1p(-p)), forest_scores.loc[name, "log_loss"])
        combined = pd.read_csv(results / "all_validation_metrics.csv").set_index("model")
        pd.testing.assert_frame_equal(combined.loc[scores.index], scores, check_names=False)
        pd.testing.assert_frame_equal(combined.loc[forest_scores.index], forest_scores, check_names=False)
        print("PASS: forest shares the original split/validation rows; reported metrics recompute;")
        print("      combined results preserve all original logistic scores; no test predictions present.")


if __name__ == "__main__":
    verify()
