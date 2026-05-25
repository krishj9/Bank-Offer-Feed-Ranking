import json
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)

def preprocess_data(df: pd.DataFrame, schema_contract: Dict[str, Any]) -> pd.DataFrame:
    """
    Preprocess the raw dataframe.
    
    - Normalizes categorical values (e.g., lowercasing, stripping whitespace)
    - Handles missing/unknown values
    - Excludes 'duration' as per contract
    - Preserves target 'y'
    
    Args:
        df: The raw dataframe.
        schema_contract: The loaded schema contract.
        
    Returns:
        The preprocessed dataframe.
    """
    logger.info("Starting preprocessing...")
    processed_df = df.copy()
    
    # 1. Exclude 'duration' (leakage field)
    excluded_fields = schema_contract.get("default", {}).get("excluded_fields", ["duration"])
    for field in excluded_fields:
        if field in processed_df.columns:
            processed_df = processed_df.drop(columns=[field])
            logger.info(f"Dropped excluded field: {field}")
            
    # 2. Normalize categorical columns
    categorical_cols = processed_df.select_dtypes(include=["object", "string"]).columns
    for col in categorical_cols:
        # Lowercase and strip whitespace
        processed_df[col] = processed_df[col].astype(str).str.lower().str.strip()
        
        # In UCI dataset, "unknown" is often used for missing values.
        # We'll keep it as "unknown" but ensure it's standardized.
        # If we wanted to replace "unknown" with pd.NA, we could do it here,
        # but often in ML it's treated as a separate category.
        
    # 3. Standardize column names (replace '.' with '_')
    processed_df.columns = processed_df.columns.str.replace(".", "_", regex=False)
    
    # 4. Handle target variable 'y'
    target_col = schema_contract.get("default", {}).get("target", "y")
    if target_col in processed_df.columns:
        # Ensure target is binary 1/0 or standard yes/no
        # We will keep it as yes/no for now, or map to 1/0 if preferred.
        # Let's map to 1/0 for easier downstream modeling.
        processed_df[target_col] = processed_df[target_col].map({"yes": 1, "no": 0})
        logger.info(f"Mapped target column '{target_col}' to 1/0.")
        
    logger.info("Preprocessing complete.")
    return processed_df

def save_processed_data(df: pd.DataFrame, output_path: str | Path) -> None:
    """Save the processed dataframe to parquet or csv."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as parquet for better type preservation and compression
    df.to_parquet(path, index=False)
    logger.info(f"Processed data saved to {path}")

def generate_preprocessing_summary(df: pd.DataFrame, output_path: str | Path) -> None:
    """Generate a summary of the preprocessing step."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "final_row_count": len(df),
        "final_column_count": len(df.columns),
        "columns": list(df.columns),
        "target_distribution": df["y"].value_counts().to_dict() if "y" in df.columns else {}
    }
    
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"Preprocessing summary written to {path}")
