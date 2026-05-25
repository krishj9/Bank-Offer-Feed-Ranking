import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Exception raised for data validation errors."""
    pass

def load_schema_contract(schema_path: str | Path) -> Dict[str, Any]:
    """Load the JSON schema contract."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema contract not found at {path}")
    
    with open(path, "r") as f:
        return json.load(f)

def validate_raw_data(df: pd.DataFrame, schema_contract: Dict[str, Any]) -> None:
    """
    Validate the raw dataframe against the schema contract.
    
    Args:
        df: The raw dataframe to validate.
        schema_contract: The loaded schema contract dictionary.
        
    Raises:
        DataValidationError: If validation fails.
    """
    logger.info("Validating raw data against schema contract...")
    
    # Check required columns
    required_columns: List[Dict[str, str]] = schema_contract.get("default", {}).get("required_columns", [])
    missing_cols = []
    
    for col_def in required_columns:
        col_name = col_def["name"]
        if col_name not in df.columns:
            missing_cols.append(col_name)
            
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")
        
    # Check for unexpected nulls in critical columns (e.g., target)
    target_col = schema_contract.get("default", {}).get("target", "y")
    if target_col in df.columns and df[target_col].isnull().any():
        raise DataValidationError(f"Target column '{target_col}' contains null values.")
        
    # Check basic types (pandas inference is usually okay, but we can do a light check)
    for col_def in required_columns:
        col_name = col_def["name"]
        expected_type = col_def["type"]
        
        if col_name in df.columns:
            actual_dtype = str(df[col_name].dtype)
            # Basic mapping from JSON schema types to pandas dtypes
            if expected_type == "integer" and not actual_dtype.startswith("int"):
                logger.warning(f"Column {col_name} expected integer, got {actual_dtype}")
            elif expected_type == "number" and not (actual_dtype.startswith("float") or actual_dtype.startswith("int")):
                logger.warning(f"Column {col_name} expected number, got {actual_dtype}")
                
    logger.info("Data validation passed successfully.")

def generate_validation_summary(df: pd.DataFrame, output_path: str | Path) -> None:
    """Generate a summary of the dataset and save it to the output path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "target_distribution": df["y"].value_counts().to_dict() if "y" in df.columns else {}
    }
    
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"Validation summary written to {path}")
