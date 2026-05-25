import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from ml.features.builder import FeatureBuilder

@pytest.fixture
def mock_schema_path():
    schema = {
        "default": {
            "user_features": [
                {"name": "age", "type": "numerical"},
                {"name": "job", "type": "categorical"}
            ],
            "offer_features": [
                {"name": "offer_id", "type": "categorical"}
            ],
            "user_offer_features": [
                {"name": "is_eligible", "type": "boolean"}
            ],
            "context_features": [
                {"name": "month", "type": "categorical"}
            ],
            "label": {
                "name": "y",
                "type": "boolean"
            },
            "excluded_features": ["duration", "leakage_col"]
        }
    }
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        json.dump(schema, f)
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink()

def test_feature_builder_inference(mock_schema_path):
    builder = FeatureBuilder(mock_schema_path)
    
    df_in = pd.DataFrame({
        "age": [25, None],
        "job": ["admin", None],
        "offer_id": ["O1", "O2"],
        "is_eligible": [True, False],
        "month": ["jan", "feb"],
        "duration": [100, 200],  # Should be excluded
        "leakage_col": [1, 2],    # Should be excluded
        "extra_col": [5, 6]       # Should be excluded
    })
    
    out_df = builder.build_features(df_in, is_training=False)
    
    # Verify expected columns exactly match
    expected_cols = ["age", "job", "offer_id", "is_eligible", "month"]
    assert list(out_df.columns) == expected_cols
    
    # Verify deterministic filling and casting
    assert out_df["age"].iloc[1] == 0.0  # NaN filled with 0.0
    assert out_df["job"].iloc[1] == "missing"  # None filled with missing
    assert out_df["is_eligible"].dtype == bool

def test_feature_builder_training(mock_schema_path):
    builder = FeatureBuilder(mock_schema_path)
    
    df_in = pd.DataFrame({
        "age": [25],
        "job": ["admin"],
        "offer_id": ["O1"],
        "is_eligible": [True],
        "month": ["jan"],
        "y": [True]
    })
    
    out_df = builder.build_features(df_in, is_training=True)
    
    expected_cols = ["age", "job", "offer_id", "is_eligible", "month", "y"]
    assert list(out_df.columns) == expected_cols
    assert out_df["y"].dtype == bool

def test_missing_required_columns(mock_schema_path):
    builder = FeatureBuilder(mock_schema_path)
    
    df_in = pd.DataFrame({
        "age": [25]
        # missing other required columns
    })
    
    with pytest.raises(ValueError, match="Missing required columns for feature building"):
        builder.build_features(df_in, is_training=False)

def test_deterministic_output(mock_schema_path):
    """Output should be deterministic regardless of input column order."""
    builder = FeatureBuilder(mock_schema_path)
    
    df_in1 = pd.DataFrame({
        "age": [25], "job": ["admin"], "offer_id": ["O1"], 
        "is_eligible": [True], "month": ["jan"]
    })
    
    # Scrambled column order
    df_in2 = pd.DataFrame({
        "month": ["jan"], "is_eligible": [True], 
        "offer_id": ["O1"], "job": ["admin"], "age": [25]
    })
    
    out1 = builder.build_features(df_in1, is_training=False)
    out2 = builder.build_features(df_in2, is_training=False)
    
    # DataFrame equality ensures columns and values match exactly
    pd.testing.assert_frame_equal(out1, out2)
