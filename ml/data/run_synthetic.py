import argparse
import pandas as pd
from pathlib import Path
from ml.data.offers import generate_offers, save_offers
from ml.data.pairs import generate_user_offer_pairs, save_pairs_and_report
from ml.data.labels import generate_synthetic_labels, save_labels_and_report

def main():
    parser = argparse.ArgumentParser(description="Run synthetic data generation pipeline.")
    parser.add_argument("--users", default="data/processed/bank_processed.parquet", help="Path to processed users parquet.")
    parser.add_argument("--offers-out", default="data/synthetic/offers.csv", help="Path to output synthetic offers.")
    parser.add_argument("--pairs-out", default="data/synthetic/user_offer_pairs.parquet", help="Path to output user-offer pairs.")
    parser.add_argument("--report-out", default="output/reports/pair_generation_report.json", help="Path to output pair generation report.")
    parser.add_argument("--labels-report-out", default="output/reports/label_generation_report.json", help="Path to output label generation report.")
    
    args = parser.parse_args()
    
    # T-012: Generate Offers
    print("Generating synthetic offers...")
    offers = generate_offers()
    save_offers(offers, args.offers_out)
    
    # T-014: Pair Generation Pipeline
    print(f"Loading users from {args.users}...")
    if not Path(args.users).exists():
        print(f"Error: Users file not found at {args.users}. Please run preprocessing first.")
        return
        
    users_df = pd.read_parquet(args.users)
    # Ensure users have an ID
    if "id" not in users_df.columns:
        users_df = users_df.reset_index().rename(columns={"index": "id"})
        users_df["id"] = users_df["id"].astype(str)
        
    print("Generating user-offer candidates...")
    pairs_df = generate_user_offer_pairs(users_df, offers)
    
    active_offers_count = sum(1 for o in offers if o.get("active"))
    
    print("Saving pairs and report...")
    save_pairs_and_report(
        pairs_df=pairs_df,
        users_count=len(users_df),
        offers_count=active_offers_count,
        pairs_output_path=args.pairs_out,
        report_output_path=args.report_out
    )
    
    # T-015: Synthetic Label Generation
    print("Generating synthetic labels...")
    offers_df = pd.DataFrame(offers)
    labeled_pairs_df = generate_synthetic_labels(pairs_df, users_df, offers_df)
    
    print("Saving labeled pairs and report...")
    save_labels_and_report(
        labeled_pairs_df=labeled_pairs_df,
        output_path=args.pairs_out,
        report_output_path=args.labels_report_out
    )
    
    print("Synthetic data generation pipeline complete.")

if __name__ == "__main__":
    main()
