import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

class FeatureBuilder:
    """
    Reusable transformation code for feature engineering,
    shared by both training and inference paths to prevent skew.
    """
    
    def __init__(self, schema_path: str | Path):
        with open(schema_path, 'r') as f:
            self.schema = json.load(f).get("default", {})
        
        self.user_features = self.schema.get("user_features", [])
        self.offer_features = self.schema.get("offer_features", [])
        self.user_offer_features = self.schema.get("user_offer_features", [])
        self.context_features = self.schema.get("context_features", [])
        
        self.label_info = self.schema.get("label", {})
        self.excluded_features = set(self.schema.get("excluded_features", []))

    def get_feature_names(self, include_label: bool = False) -> List[str]:
        """Returns ordered list of expected features."""
        features = []
        for feature_group in [self.user_features, self.offer_features, self.user_offer_features, self.context_features]:
            for f in feature_group:
                features.append(f["name"])
                
        if include_label and self.label_info:
            features.append(self.label_info["name"])
            
        return [f for f in features if f not in self.excluded_features]
    
    def get_feature_types(self) -> Dict[str, str]:
        """Returns mapping from feature name to schema type."""
        feature_types = {}
        for feature_group in [self.user_features, self.offer_features, self.user_offer_features, self.context_features]:
            for f in feature_group:
                feature_types[f["name"]] = f["type"]
        if self.label_info:
             feature_types[self.label_info["name"]] = self.label_info["type"]
        return feature_types

    def build_features(self, df: pd.DataFrame, is_training: bool = False) -> pd.DataFrame:
        """
        Transform raw input dataframe into model-ready features.
        Used for both training (is_training=True) and inference (is_training=False).
        
        Args:
            df: Input dataframe containing raw feature columns.
            is_training: Whether to include label column.
            
        Returns:
            pd.DataFrame with deterministic column order and types.
        """
        df = df.copy()
        
        expected_cols = self.get_feature_names(include_label=is_training)
        
        # Check for missing required columns
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns for feature building: {missing_cols}")
            
        # Select and reorder columns deterministically
        out_df = df[expected_cols].copy()
        
        # Explicitly ensure excluded features like duration are removed
        # (Though they shouldn't be in expected_cols anyway, but as an extra safety measure)
        for excl in self.excluded_features:
            if excl in out_df.columns:
                out_df = out_df.drop(columns=[excl])
                
        # Type casting and deterministic null filling based on schema
        feature_types = self.get_feature_types()
        for col in out_df.columns:
            ftype = feature_types.get(col)
            if ftype == "numerical":
                out_df[col] = pd.to_numeric(out_df[col], errors='coerce').fillna(0.0)
            elif ftype == "categorical":
                # Ensure missing values are represented as string "missing" rather than nan
                out_df[col] = out_df[col].fillna("missing").astype(str)
                # If there were any actual string "nan" or "None" they will just be strings.
                # Standardizing real nans to "missing" first is safer.
            elif ftype == "boolean":
                out_df[col] = out_df[col].astype(bool)
                
        return out_df
