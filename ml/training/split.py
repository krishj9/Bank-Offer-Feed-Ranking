import json
from pathlib import Path
from typing import Tuple, Dict, Any

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split


def split_data(
    df: pd.DataFrame, 
    test_size: float = 0.2, 
    random_state: int = 42,
    group_col: str = "user_id"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Split the data into train and validation sets.
    If group_col is present, ensures users are strictly in either train or val,
    preventing data leakage across users.
    
    Args:
        df: The dataset to split.
        test_size: Fraction of data to use for validation.
        random_state: Seed for reproducibility.
        group_col: The column to group by (e.g. user_id).
        
    Returns:
        train_df: Training data.
        val_df: Validation data.
        stats: Dictionary of split statistics.
    """
    if group_col in df.columns:
        gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
        train_idx, val_idx = next(gss.split(df, groups=df[group_col]))
        train_df = df.iloc[train_idx].copy()
        val_df = df.iloc[val_idx].copy()
    else:
        # Fallback to random split
        train_df, val_df = train_test_split(
            df, test_size=test_size, random_state=random_state
        )
        
    stats = {
        "total_rows": len(df),
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "train_ratio": len(train_df) / len(df) if len(df) > 0 else 0,
        "test_size_config": test_size,
        "random_state": random_state,
        "grouped_by": group_col if group_col in df.columns else None
    }
    
    return train_df, val_df, stats


def save_split_report(stats: Dict[str, Any], output_path: str | Path):
    """
    Save the split statistics report to a JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Saved split strategy report to {output_path}")
