import argparse
import pandas as pd
from pathlib import Path

from ml.training.split import split_data, save_split_report
from ml.training.train import train_baseline_model, save_artifacts
from ml.evaluation.evaluate import evaluate_model, save_evaluation_metrics

def main():
    parser = argparse.ArgumentParser(description="Run baseline model training pipeline.")
    parser.add_argument("--users", default="data/processed/bank_processed.parquet", help="Path to processed users data")
    parser.add_argument("--offers", default="data/synthetic/offers.csv", help="Path to offers data")
    parser.add_argument("--pairs", default="data/synthetic/user_offer_pairs.parquet", help="Path to labeled user-offer pairs")
    parser.add_argument("--schema", default="shared/contracts/feature_schema.json", help="Path to feature schema")
    
    parser.add_argument("--split-report-out", default="output/reports/split_report.json", help="Output path for split report")
    parser.add_argument("--model-out-dir", default="ml/artifacts/", help="Output directory for model artifacts")
    parser.add_argument("--metrics-out", default="output/metrics/evaluation_metrics.json", help="Output path for metrics")
    parser.add_argument("--eval-report-out", default="output/reports/evaluation_report.json", help="Output path for evaluation report")
    
    args = parser.parse_args()
    
    print("Loading data...")
    try:
        users_df = pd.read_parquet(args.users)
        offers_df = pd.read_csv(args.offers)
        pairs_df = pd.read_parquet(args.pairs)
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return
        
    # Ensure users have an id column
    if "id" not in users_df.columns:
        users_df = users_df.reset_index().rename(columns={"index": "id"})
    users_df["id"] = users_df["id"].astype(str)
    pairs_df["user_id"] = pairs_df["user_id"].astype(str)
    
    print("Merging data for feature building...")
    df = pairs_df.merge(users_df, left_on="user_id", right_on="id", how="left")
    df = df.merge(offers_df, on="offer_id", how="left")
    
    # Check for target column 'label' vs 'y'
    # The pairs script generated 'label' based on inspect output
    if "label" in df.columns and "y" not in df.columns:
        df = df.rename(columns={"label": "y"})
        
    # Ensure missing user_offer_features exist before building
    if "eligible" in df.columns and "is_eligible" not in df.columns:
        df["is_eligible"] = df["eligible"]
    if "affinity_score" not in df.columns:
        df["affinity_score"] = 0.5  # placeholder
        
    print(f"Total labeled pairs: {len(df)}")
    
    # T-018: Train-validation split strategy
    print("Splitting data...")
    train_df, val_df, split_stats = split_data(df, test_size=0.2, group_col="user_id")
    save_split_report(split_stats, args.split_report_out)
    
    # T-019: Baseline model trainer
    print("Training baseline model...")
    hyperparams = {
        "max_iter": 100,
        "learning_rate": 0.1,
        "max_depth": 6,
        "random_state": 42
    }
    model, builder, feature_names = train_baseline_model(
        train_df=train_df,
        schema_path=args.schema,
        hyperparameters=hyperparams
    )
    
    save_artifacts(
        model=model,
        builder=builder,
        feature_names=feature_names,
        model_out_dir=args.model_out_dir,
        manifest_path=Path(args.model_out_dir) / "run_manifest.json",
        metadata={"split_stats": split_stats}
    )
    
    # T-020: Offline evaluation
    print("Evaluating model...")
    metrics = evaluate_model(model, builder, val_df, k=3)
    save_evaluation_metrics(metrics, args.metrics_out, args.eval_report_out)
    
    print("Pipeline complete.")

if __name__ == "__main__":
    main()
