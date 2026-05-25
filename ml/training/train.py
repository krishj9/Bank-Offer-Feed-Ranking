import json
import joblib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from ml.features.builder import FeatureBuilder

def train_baseline_model(
    train_df: pd.DataFrame, 
    schema_path: str,
    hyperparameters: Dict[str, Any] = None
) -> Tuple[HistGradientBoostingClassifier, FeatureBuilder, list]:
    """
    Train a baseline HistGradientBoostingClassifier ranking/classification model.
    """
    if hyperparameters is None:
        hyperparameters = {
            "max_iter": 100,
            "learning_rate": 0.1,
            "max_depth": 5,
            "random_state": 42
        }
        
    builder = FeatureBuilder(schema_path)
    
    # Extract features using the shared feature builder
    X_train_full = builder.build_features(train_df, is_training=True)
    
    # Schema defines the target name, usually 'y'
    target_col = builder.label_info.get("name", "y")
    
    if target_col not in X_train_full.columns:
        raise ValueError(f"Target column '{target_col}' not found in training data after feature generation.")
        
    y_train = X_train_full[target_col]
    X_train = X_train_full.drop(columns=[target_col])
    
    # Find categorical features for HistGradientBoostingClassifier
    categorical_features = []
    feature_types = builder.get_feature_types()
    for col in X_train.columns:
        if feature_types.get(col) == "categorical":
            X_train[col] = X_train[col].astype("category")
            categorical_features.append(col)
            
    if categorical_features:
        hyperparameters["categorical_features"] = categorical_features
            
    # Train model
    print("Training HistGradientBoostingClassifier model...")
    model = HistGradientBoostingClassifier(**hyperparameters)
    model.fit(X_train, y_train)
    
    # Return model, builder, and expected feature names
    return model, builder, list(X_train.columns)

def save_artifacts(
    model: HistGradientBoostingClassifier,
    builder: FeatureBuilder,
    feature_names: list,
    model_out_dir: str | Path,
    manifest_path: str | Path,
    metadata: Dict[str, Any] = None
):
    """
    Save the model, feature schema info, and run manifest.
    """
    model_out_dir = Path(model_out_dir)
    model_out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = model_out_dir / "baseline_model.joblib"
    joblib.dump(model, model_path)
    
    # Save preprocessor artifact (just the schema we used)
    preprocessor_path = model_out_dir / "preprocessor.json"
    with open(preprocessor_path, "w") as f:
        json.dump(builder.schema, f, indent=2)
        
    # Create run manifest
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "model_type": "HistGradientBoostingClassifier",
        "hyperparameters": {k: v for k, v in model.get_params().items() if k != "categorical_features"},
        "feature_names": feature_names,
        "artifacts": {
            "model": str(model_path),
            "preprocessor": str(preprocessor_path)
        }
    }
    
    if metadata:
        manifest.update(metadata)
        
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Saved artifacts to {model_out_dir} and manifest to {manifest_path}")
    return manifest
