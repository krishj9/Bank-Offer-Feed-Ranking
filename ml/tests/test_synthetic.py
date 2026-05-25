import pytest
import pandas as pd
from ml.data.offers import generate_offers
from ml.data.eligibility import check_eligibility
from ml.data.pairs import generate_user_offer_pairs
from ml.data.labels import generate_synthetic_labels

def test_generate_offers():
    offers = generate_offers()
    assert len(offers) >= 5
    for offer in offers:
        assert "offer_id" in offer
        assert "offer_type" in offer
        assert "eligibility_rules" in offer

def test_eligibility_engine():
    offer = {
        "offer_id": "TEST-1",
        "eligibility_rules": {
            "min_age": 25,
            "marital": ["single"],
            "housing": "yes"
        }
    }
    
    # Eligible user
    user1 = {"age": 26, "marital": "single", "housing": "yes"}
    is_eligible, reasons = check_eligibility(user1, offer)
    assert is_eligible
    assert len(reasons) == 0
    
    # Ineligible user (age)
    user2 = {"age": 24, "marital": "single", "housing": "yes"}
    is_eligible, reasons = check_eligibility(user2, offer)
    assert not is_eligible
    assert len(reasons) > 0
    assert any("age" in r for r in reasons)
    
    # Ineligible user (marital)
    user3 = {"age": 30, "marital": "married", "housing": "yes"}
    is_eligible, reasons = check_eligibility(user3, offer)
    assert not is_eligible
    assert len(reasons) > 0

def test_pair_generation():
    offers = [
        {"offer_id": "O-1", "active": True, "eligibility_rules": {"min_age": 30}},
        {"offer_id": "O-2", "active": True, "eligibility_rules": {"housing": "no"}},
        {"offer_id": "O-3", "active": False, "eligibility_rules": {}}
    ]
    
    users = pd.DataFrame([
        {"id": "U-1", "age": 35, "housing": "yes"},
        {"id": "U-2", "age": 25, "housing": "no"}
    ])
    
    pairs_df = generate_user_offer_pairs(users, offers)
    
    assert len(pairs_df) == 2
    # U-1 matches O-1 (age>=30) but not O-2 (housing=yes)
    assert ((pairs_df["user_id"] == "U-1") & (pairs_df["offer_id"] == "O-1")).any()
    # U-2 matches O-2 (housing=no) but not O-1 (age<30)
    assert ((pairs_df["user_id"] == "U-2") & (pairs_df["offer_id"] == "O-2")).any()
    # O-3 should not be in pairs because it's inactive
    assert not (pairs_df["offer_id"] == "O-3").any()

def test_synthetic_labels():
    pairs_df = pd.DataFrame([
        {"user_id": "U-1", "offer_id": "O-1", "eligible": True},
        {"user_id": "U-2", "offer_id": "O-2", "eligible": True},
        {"user_id": "U-3", "offer_id": "O-3", "eligible": True},
    ])
    
    users_df = pd.DataFrame([
        {"id": "U-1", "y": 1, "campaign": 1, "age": 35, "job": "management", "default": "no", "housing": "no", "loan": "no", "pdays": 999},
        {"id": "U-2", "y": 0, "campaign": 6, "age": 25, "job": "student", "default": "no", "housing": "yes", "loan": "no", "pdays": 999},
        {"id": "U-3", "y": 1, "campaign": 2, "age": 55, "job": "retired", "default": "no", "housing": "yes", "loan": "yes", "pdays": 5},
    ])
    
    offers_df = pd.DataFrame([
        {"offer_id": "O-1", "offer_type": "term_deposit_reminder", "category": "savings"},
        {"offer_id": "O-2", "offer_type": "savings_boost", "category": "savings"},
        {"offer_id": "O-3", "offer_type": "advisor_callback", "category": "advice"},
    ])
    
    labeled_df = generate_synthetic_labels(pairs_df, users_df, offers_df)
    
    assert "label" in labeled_df.columns
    assert len(labeled_df) == 3
    
    # Check that labels are 0 or 1
    assert set(labeled_df["label"].unique()).issubset({0, 1})
