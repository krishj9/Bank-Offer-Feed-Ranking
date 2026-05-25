import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any
from ml.data.eligibility import check_eligibility

def generate_user_offer_pairs(users_df: pd.DataFrame, offers: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Generate eligible user-offer candidates.
    Takes users DataFrame and list of offers.
    Returns a DataFrame of eligible pairs.
    """
    pairs = []
    
    # Iterate through users
    for _, user_row in users_df.iterrows():
        user_dict = user_row.to_dict()
        user_id = user_dict.get("id", user_row.name)  # Fallback to index if no id
        
        for offer in offers:
            if not offer.get("active", False):
                continue
                
            is_eligible, reasons = check_eligibility(user_dict, offer)
            
            if is_eligible:
                pair = {
                    "user_id": user_id,
                    "offer_id": offer["offer_id"],
                    "eligible": True
                }
                pairs.append(pair)
                
    return pd.DataFrame(pairs)

def save_pairs_and_report(pairs_df: pd.DataFrame, users_count: int, offers_count: int, pairs_output_path: str, report_output_path: str):
    """
    Save the pairs to parquet and write a report.
    """
    Path(pairs_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save pairs
    pairs_df.to_parquet(pairs_output_path, index=False)
    print(f"Saved {len(pairs_df)} eligible pairs to {pairs_output_path}")
    
    # Generate report
    total_possible_pairs = users_count * offers_count
    eligible_count = len(pairs_df)
    coverage = eligible_count / total_possible_pairs if total_possible_pairs > 0 else 0
    
    report = {
        "users_count": users_count,
        "active_offers_count": offers_count,
        "total_possible_pairs": total_possible_pairs,
        "eligible_pairs_generated": eligible_count,
        "eligibility_coverage": coverage
    }
    
    with open(report_output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved pair generation report to {report_output_path}")
