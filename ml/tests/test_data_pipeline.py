import json
from pathlib import Path

import pandas as pd
import pytest

from ml.data.loaders import load_raw_bank_data
from ml.data.validation import validate_raw_data, DataValidationError
from ml.data.preprocess import preprocess_data
from ml.data.sample_users import extract_sample_users

@pytest.fixture
def mock_schema_contract():
    return {
        "default": {
            "target": "y",
            "excluded_fields": ["duration"],
            "required_columns": [
                {"name": "age", "type": "integer"},
                {"name": "job", "type": "string"},
                {"name": "duration", "type": "integer"},
                {"name": "y", "type": "string"}
            ]
        }
    }

@pytest.fixture
def mock_raw_data():
    return pd.DataFrame({
        "age": [25, 35, 45],
        "job": ["admin.", "blue-collar", "technician"],
        "duration": [100, 200, 300],
        "y": ["no", "yes", "no"]
    })

def test_load_raw_bank_data(tmp_path):
    # Create a dummy CSV
    csv_path = tmp_path / "dummy.csv"
    csv_path.write_text("age;job;duration;y\n25;admin.;100;no\n")
    
    df = load_raw_bank_data(csv_path)
    assert len(df) == 1
    assert list(df.columns) == ["age", "job", "duration", "y"]

def test_validate_raw_data_success(mock_raw_data, mock_schema_contract):
    # Should not raise an exception
    validate_raw_data(mock_raw_data, mock_schema_contract)

def test_validate_raw_data_missing_column(mock_raw_data, mock_schema_contract):
    df_missing = mock_raw_data.drop(columns=["age"])
    with pytest.raises(DataValidationError, match="Missing required columns"):
        validate_raw_data(df_missing, mock_schema_contract)

def test_preprocess_data(mock_raw_data, mock_schema_contract):
    processed = preprocess_data(mock_raw_data, mock_schema_contract)
    
    # Check duration is removed
    assert "duration" not in processed.columns
    
    # Check categorical normalization (e.g., 'admin.' -> 'admin.')
    # Actually our preprocess replaces '.' with '_' in column names, not values,
    # but it lowers and strips values.
    assert processed["job"].iloc[0] == "admin."
    
    # Check target mapping
    assert processed["y"].tolist() == [0, 1, 0]

def test_extract_sample_users(mock_raw_data, mock_schema_contract):
    processed = preprocess_data(mock_raw_data, mock_schema_contract)
    samples = extract_sample_users(processed, n_samples=2, random_state=42)
    
    assert len(samples) == 2
    assert "user_id" in samples.columns
    assert samples["user_id"].iloc[0].startswith("demo_user_")
