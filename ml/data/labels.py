import pandas as pd
import json
import hashlib
from pathlib import Path
from typing import Dict, Any

def generate_synthetic_labels(pairs_df: pd.DataFrame, users_df: pd.DataFrame, offers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate synthetic labels for user-offer pairs deterministically.
    
    Args:
        pairs_df: DataFrame containing user_id, offer_id, eligible
        users_df: DataFrame containing user features including target 'y', 'campaign', 'housing', 'loan', 'job', 'default', 'pdays', 'age'
        offers_df: DataFrame containing offer_id, offer_type, category
        
    Returns:
        DataFrame with added 'label' column (1 or 0)
    """
    # Merge user features and offer features into pairs
    df = pairs_df.merge(users_df, left_on='user_id', right_on='id', how='left')
    df = df.merge(offers_df[['offer_id', 'offer_type', 'category']], on='offer_id', how='left')
    
    labels = []
    
    for _, row in df.iterrows():
        label = 0
        
        # Original target y
        y = row.get('y', 0)
        offer_type = row.get('offer_type', '')
        category = row.get('category', '')
        
        # Campaign-related heuristics
        campaign = row.get('campaign', 0)
        pdays = row.get('pdays', 999)
        
        # User features
        job = row.get('job', 'unknown')
        default = row.get('default', 'unknown')
        housing = row.get('housing', 'unknown')
        loan = row.get('loan', 'unknown')
        age = row.get('age', 0)
        
        # Base logic by offer_type
        if offer_type == 'term_deposit_reminder':
            # Direct mapping from original dataset target
            label = y
        elif offer_type == 'savings_boost':
            # Likely to accept if they accepted term deposit and haven't been over-contacted
            if y == 1 and campaign <= 3:
                label = 1
        elif offer_type == 'credit_card_upgrade':
            # High-income jobs and no default
            if job in ['management', 'entrepreneur', 'admin.', 'technician'] and default == 'no':
                label = 1
        elif offer_type == 'refinance_prompt':
            # Needs to have a housing loan, maybe another loan
            if housing == 'yes' and loan == 'yes':
                label = 1
            elif housing == 'yes' and age > 30 and y == 1:
                label = 1
        elif offer_type == 'advisor_callback':
            # Older users or previously contacted users
            if age >= 45 and pdays != 999:
                label = 1
            elif y == 1 and age >= 50:
                label = 1
        
        # Negative label heuristics (Overrides)
        # If contacted too many times in the current campaign, they are fatigued
        if campaign > 5:
            label = 0
            
        # If they have credit default, do not give them credit offers
        if default == 'yes' and category == 'credit':
            label = 0
            
        # Deterministic noise: flip 5% of labels to add realism
        # Use hash of user_id and offer_id for determinism
        hash_str = f"{row['user_id']}_{row['offer_id']}"
        hash_val = int(hashlib.md5(hash_str.encode('utf-8')).hexdigest(), 16)
        if hash_val % 100 < 5:
            label = 1 - label
            
        labels.append(label)
        
    # Create result dataframe
    result_df = pairs_df.copy()
    result_df['label'] = labels
    
    return result_df

def save_labels_and_report(labeled_pairs_df: pd.DataFrame, output_path: str, report_output_path: str):
    """
    Save the labeled pairs to parquet and write a report of assumptions and label distribution.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save labeled pairs
    labeled_pairs_df.to_parquet(output_path, index=False)
    print(f"Saved {len(labeled_pairs_df)} labeled pairs to {output_path}")
    
    # Generate report
    total_pairs = len(labeled_pairs_df)
    positive_count = int(labeled_pairs_df['label'].sum())
    negative_count = total_pairs - positive_count
    positive_rate = positive_count / total_pairs if total_pairs > 0 else 0
    
    report = {
        "total_pairs": total_pairs,
        "positive_labels": positive_count,
        "negative_labels": negative_count,
        "positive_rate": positive_rate,
        "assumptions": [
            "term_deposit_reminder: Uses original target 'y'.",
            "savings_boost: Positive if y=1 and campaign <= 3.",
            "credit_card_upgrade: Positive if job is management/entrepreneur/admin/technician and no default.",
            "refinance_prompt: Positive if housing=yes and (loan=yes or (age>30 and y=1)).",
            "advisor_callback: Positive if age>=45 and previously contacted (pdays!=999), or y=1 and age>=50.",
            "Negative heuristic: Force label=0 if campaign > 5 (fatigue).",
            "Negative heuristic: Force label=0 if default=yes and category=credit.",
            "Noise: Deterministically flipped 5% of labels using hash(user_id + offer_id) for realism."
        ]
    }
    
    with open(report_output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved label generation report to {report_output_path}")
