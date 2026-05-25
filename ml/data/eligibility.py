from typing import Dict, Any, Tuple, List

def check_eligibility(user: Dict[str, Any], offer: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Deterministic eligibility engine.
    Takes a user dictionary and an offer dictionary.
    Returns (is_eligible, debug_reasons_list).
    """
    reasons = []
    rules = offer.get("eligibility_rules", {})
    
    # Check minimum age
    if "min_age" in rules:
        if user.get("age", 0) < rules["min_age"]:
            reasons.append(f"User age {user.get('age')} is less than min_age {rules['min_age']}")
            
    # Check maximum age
    if "max_age" in rules:
        if user.get("age", 0) > rules["max_age"]:
            reasons.append(f"User age {user.get('age')} is greater than max_age {rules['max_age']}")
            
    # Check excluded jobs
    if "exclude_jobs" in rules:
        if user.get("job") in rules["exclude_jobs"]:
            reasons.append(f"User job '{user.get('job')}' is in excluded jobs {rules['exclude_jobs']}")
            
    # Check marital status
    if "marital" in rules:
        if user.get("marital") not in rules["marital"]:
            reasons.append(f"User marital status '{user.get('marital')}' not in required {rules['marital']}")
            
    # Check education
    if "education" in rules:
        # Simple string match or list match
        req_edu = rules["education"]
        if isinstance(req_edu, list):
            if user.get("education") not in req_edu:
                reasons.append(f"User education '{user.get('education')}' not in {req_edu}")
        else:
            if user.get("education") != req_edu:
                reasons.append(f"User education '{user.get('education')}' != {req_edu}")
                
    # Check housing
    if "housing" in rules:
        if user.get("housing") != rules["housing"]:
            reasons.append(f"User housing '{user.get('housing')}' != {rules['housing']}")
            
    # Check loan
    if "loan" in rules:
        if user.get("loan") != rules["loan"]:
            reasons.append(f"User loan '{user.get('loan')}' != {rules['loan']}")
            
    is_eligible = len(reasons) == 0
    return is_eligible, reasons
