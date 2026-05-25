import json
from pathlib import Path
from typing import Dict, Any

import numpy as pd
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, log_loss

def calculate_ranking_metrics_per_user(user_group: pd.DataFrame, k: int = 3) -> Dict[str, float]:
    """
    Calculate Precision@K, Recall@K, MAP@K, NDCG@K for a single user's offers.
    Expects columns: 'y_true' and 'y_pred'.
    """
    # Sort by predicted probability descending
    sorted_group = user_group.sort_values(by="y_pred", ascending=False).head(k)
    y_true_sorted = sorted_group["y_true"].values
    
    # All true positive items for this user in the whole group
    total_positives = user_group["y_true"].sum()
    
    if total_positives == 0:
        # If user has no relevant items, metrics are generally undefined or 0.
        # Often we return 0.0 or exclude them from averages. We will return 0.0.
        return {"precision@k": 0.0, "recall@k": 0.0, "map@k": 0.0, "ndcg@k": 0.0}
        
    # Precision@K
    precision_k = y_true_sorted.sum() / k
    
    # Recall@K
    recall_k = y_true_sorted.sum() / total_positives
    
    # Average Precision@K
    hits = 0
    sum_precisions = 0.0
    for i, p in enumerate(y_true_sorted):
        if p == 1:
            hits += 1
            sum_precisions += hits / (i + 1)
    ap_k = sum_precisions / min(k, total_positives)
    
    # NDCG@K
    dcg = 0.0
    for i, p in enumerate(y_true_sorted):
        if p == 1:
            dcg += 1.0 / np.log2(i + 2)
            
    # IDCG@K
    idcg = 0.0
    for i in range(min(k, int(total_positives))):
        idcg += 1.0 / np.log2(i + 2)
        
    ndcg_k = dcg / idcg if idcg > 0 else 0.0
    
    return {
        "precision@k": float(precision_k),
        "recall@k": float(recall_k),
        "map@k": float(ap_k),
        "ndcg@k": float(ndcg_k)
    }


def evaluate_model(
    model, 
    builder, 
    val_df: pd.DataFrame, 
    k: int = 3
) -> Dict[str, Any]:
    """
    Evaluate the model using classification and ranking metrics.
    """
    # Build features
    X_val_full = builder.build_features(val_df, is_training=True)
    target_col = builder.label_info.get("name", "y")
    
    y_true = X_val_full[target_col].astype(int)
    X_val = X_val_full.drop(columns=[target_col])
    
    # Convert types for LightGBM if needed
    feature_types = builder.get_feature_types()
    for col in X_val.columns:
        if feature_types.get(col) == "categorical":
            X_val[col] = X_val[col].astype("category")
            
    # Predict
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    
    # Classification metrics
    auc = roc_auc_score(y_true, y_pred_proba)
    ll = log_loss(y_true, y_pred_proba)
    
    # Ranking metrics
    # We need user_id to group predictions
    if "user_id" not in val_df.columns:
        # Fallback if no user_id available: just return classification metrics
        print("Warning: 'user_id' not found in validation data. Skipping ranking metrics.")
        return {
            "classification": {"auc": float(auc), "log_loss": float(ll)},
            "ranking": {}
        }
        
    eval_df = pd.DataFrame({
        "user_id": val_df["user_id"].values,
        "y_true": y_true.values,
        "y_pred": y_pred_proba
    })
    
    # Group by user_id and calculate metrics
    user_metrics = eval_df.groupby("user_id").apply(lambda g: calculate_ranking_metrics_per_user(g, k=k))
    
    # user_metrics is a Series of dicts
    avg_precision_k = user_metrics.apply(lambda x: x["precision@k"]).mean()
    avg_recall_k = user_metrics.apply(lambda x: x["recall@k"]).mean()
    avg_map_k = user_metrics.apply(lambda x: x["map@k"]).mean()
    avg_ndcg_k = user_metrics.apply(lambda x: x["ndcg@k"]).mean()
    
    metrics = {
        "classification": {
            "auc": float(auc),
            "log_loss": float(ll)
        },
        "ranking": {
            f"precision@{k}": float(avg_precision_k),
            f"recall@{k}": float(avg_recall_k),
            f"map@{k}": float(avg_map_k),
            f"ndcg@{k}": float(avg_ndcg_k)
        }
    }
    
    return metrics


def save_evaluation_metrics(metrics: Dict[str, Any], metrics_out: str | Path, report_out: str | Path):
    """
    Save evaluation metrics and report.
    """
    metrics_out = Path(metrics_out)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    
    report_out = Path(report_out)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metrics_out, "w") as f:
        json.dump(metrics, f, indent=2)
        
    with open(report_out, "w") as f:
        json.dump({
            "summary": "Offline Evaluation Report",
            "metrics": metrics
        }, f, indent=2)
        
    print(f"Saved evaluation metrics to {metrics_out} and report to {report_out}")
