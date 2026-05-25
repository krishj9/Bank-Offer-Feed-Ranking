import pandas as pd
import pytest

from ml.evaluation.evaluate import calculate_ranking_metrics_per_user


def test_calculate_ranking_metrics_per_user():
    # User with 3 true positives
    df = pd.DataFrame({
        "y_true": [1, 0, 1, 0, 1],
        "y_pred": [0.9, 0.8, 0.7, 0.6, 0.5]
    })

    metrics = calculate_ranking_metrics_per_user(df, k=3)

    # Top 3 are indices 0, 1, 2
    # y_true sorted by y_pred: [1, 0, 1, 0, 1]
    # At k=3, y_true is [1, 0, 1]
    # Precision@3 = 2 / 3
    assert metrics["precision@k"] == pytest.approx(2/3)

    # Recall@3 = 2 / 3 (total positives = 3)
    assert metrics["recall@k"] == pytest.approx(2/3)

    # MAP@K computation:
    # rank 1: 1 -> precision 1/1
    # rank 2: 0
    # rank 3: 1 -> precision 2/3
    # AP@3 = (1/1 + 2/3) / 3 = 1.666 / 3 = 0.555...
    assert metrics["map@k"] == pytest.approx((1 + 2/3) / 3)

def test_calculate_ranking_metrics_per_user_no_positives():
    df = pd.DataFrame({
        "y_true": [0, 0, 0],
        "y_pred": [0.9, 0.8, 0.7]
    })
    metrics = calculate_ranking_metrics_per_user(df, k=3)
    assert metrics["precision@k"] == 0.0
    assert metrics["recall@k"] == 0.0
    assert metrics["map@k"] == 0.0
    assert metrics["ndcg@k"] == 0.0

def test_save_evaluation_metrics(tmp_path):
    import json

    from ml.evaluation.evaluate import save_evaluation_metrics

    metrics = {
        "classification": {"auc": 0.85, "log_loss": 0.4},
        "ranking": {"precision@3": 0.6, "recall@3": 0.5, "map@3": 0.55, "ndcg@3": 0.58}
    }

    metrics_out = tmp_path / "metrics.json"
    report_out = tmp_path / "report.json"

    save_evaluation_metrics(metrics, metrics_out, report_out)

    assert metrics_out.exists()
    assert report_out.exists()

    with open(metrics_out) as f:
        saved_metrics = json.load(f)
    assert saved_metrics == metrics

    with open(report_out) as f:
        saved_report = json.load(f)
    assert "summary" in saved_report
    assert saved_report["metrics"] == metrics

def test_evaluate_model():
    import numpy as np
    import pandas as pd

    from ml.evaluation.evaluate import evaluate_model

    class MockModel:
        def predict_proba(self, X):
            # Return deterministic probabilities
            return np.array([[0.1, 0.9], [0.8, 0.2], [0.3, 0.7], [0.6, 0.4]])

    class MockBuilder:
        def __init__(self):
            self.label_info = {"name": "y"}
        def build_features(self, df, is_training):
            return df.copy()
        def get_feature_types(self):
            return {"feature1": "numerical"}

    val_df = pd.DataFrame({
        "user_id": ["u1", "u1", "u2", "u2"],
        "feature1": [1.0, 2.0, 3.0, 4.0],
        "y": [1, 0, 1, 0]
    })

    model = MockModel()
    builder = MockBuilder()

    metrics = evaluate_model(model, builder, val_df, k=1)

    assert "classification" in metrics
    assert "auc" in metrics["classification"]
    assert "log_loss" in metrics["classification"]

    assert "ranking" in metrics
    assert "precision@1" in metrics["ranking"]
    assert "recall@1" in metrics["ranking"]
    assert "map@1" in metrics["ranking"]
    assert "ndcg@1" in metrics["ranking"]
