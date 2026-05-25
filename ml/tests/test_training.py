import pandas as pd
import pytest
from pathlib import Path

from ml.training.split import split_data
from ml.training.train import train_baseline_model

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "user_id": ["u1", "u1", "u2", "u2", "u3", "u3", "u4", "u4"],
        "offer_id": ["o1", "o2", "o1", "o2", "o1", "o2", "o1", "o2"],
        "age": [30, 30, 40, 40, 50, 50, 60, 60],
        "job": ["admin", "admin", "blue-collar", "blue-collar", "technician", "technician", "admin", "admin"],
        "y": [1, 0, 0, 1, 1, 1, 0, 0]
    })

@pytest.fixture
def mock_schema(tmp_path):
    schema_path = tmp_path / "feature_schema.json"
    schema_content = {
        "default": {
            "user_features": [
                {"name": "age", "type": "numerical", "description": ""},
                {"name": "job", "type": "categorical", "description": ""}
            ],
            "offer_features": [],
            "user_offer_features": [],
            "context_features": [],
            "label": {"name": "y", "type": "boolean", "description": ""},
            "excluded_features": ["duration"]
        }
    }
    import json
    with open(schema_path, "w") as f:
        json.dump(schema_content, f)
    return schema_path

def test_split_data(sample_data):
    train_df, val_df, stats = split_data(sample_data, test_size=0.25, group_col="user_id", random_state=42)
    
    assert len(train_df) + len(val_df) == len(sample_data)
    assert stats["train_rows"] == len(train_df)
    
    # Check that users are not overlapping
    train_users = set(train_df["user_id"])
    val_users = set(val_df["user_id"])
    assert len(train_users.intersection(val_users)) == 0

def test_train_baseline_model(sample_data, mock_schema):
    model, builder, feature_names = train_baseline_model(
        train_df=sample_data,
        schema_path=mock_schema,
        hyperparameters={"max_iter": 5, "random_state": 42}
    )
    
    assert model is not None
    assert builder is not None
    assert "age" in feature_names
    assert "job" in feature_names
    assert "y" not in feature_names
