import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any

def generate_offers() -> List[Dict[str, Any]]:
    """
    Generate synthetic bank offer catalog with at least five distinct offer types.
    Matches shared/contracts/offer_schema.json.
    """
    offers = [
        {
            "offer_id": "OFR-001",
            "offer_type": "term_deposit_reminder",
            "title": "Lock in a High-Yield Term Deposit",
            "description": "Secure your savings with our market-leading term deposit rate.",
            "category": "savings",
            "priority_weight": 1.0,
            "active": True,
            "eligibility_rules": {
                "min_age": 25,
                "exclude_jobs": ["student", "unemployed"]
            },
            "version": "1.0"
        },
        {
            "offer_id": "OFR-002",
            "offer_type": "savings_boost",
            "title": "Savings Rate Boost",
            "description": "Earn extra interest on your savings account this month.",
            "category": "savings",
            "priority_weight": 1.2,
            "active": True,
            "eligibility_rules": {
                "max_age": 35,
                "marital": ["single"]
            },
            "version": "1.0"
        },
        {
            "offer_id": "OFR-003",
            "offer_type": "credit_card_upgrade",
            "title": "Premium Credit Card Upgrade",
            "description": "Upgrade to our premium rewards credit card with zero fees for the first year.",
            "category": "credit",
            "priority_weight": 1.5,
            "active": True,
            "eligibility_rules": {
                "min_age": 21,
                "education": ["university.degree", "professional.course"]
            },
            "version": "1.0"
        },
        {
            "offer_id": "OFR-004",
            "offer_type": "refinance_prompt",
            "title": "Refinance Your Home Loan",
            "description": "Lower your monthly payments by refinancing your mortgage today.",
            "category": "credit",
            "priority_weight": 1.8,
            "active": True,
            "eligibility_rules": {
                "housing": "yes"
            },
            "version": "1.0"
        },
        {
            "offer_id": "OFR-005",
            "offer_type": "advisor_callback",
            "title": "Free Financial Wellness Session",
            "description": "Schedule a free 30-minute callback with one of our financial advisors.",
            "category": "advice",
            "priority_weight": 0.8,
            "active": True,
            "eligibility_rules": {
                "min_age": 40,
                "loan": "no"
            },
            "version": "1.0"
        }
    ]
    return offers

def save_offers(offers: List[Dict[str, Any]], output_path: str):
    """
    Save the generated offers to a CSV file.
    Eligibility rules are serialized as JSON strings.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(offers)
    df['eligibility_rules'] = df['eligibility_rules'].apply(json.dumps)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(offers)} offers to {output_path}")

def load_offers(input_path: str) -> List[Dict[str, Any]]:
    """
    Load offers from CSV and deserialize eligibility_rules.
    """
    df = pd.read_csv(input_path)
    df['eligibility_rules'] = df['eligibility_rules'].apply(json.loads)
    return df.to_dict(orient='records')
