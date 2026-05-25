import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

def extract_sample_users(df: pd.DataFrame, n_samples: int = 10, random_state: int = 42) -> pd.DataFrame:
    """
    Extract a representative set of demo user profiles from the processed data.
    
    Args:
        df: The processed dataframe.
        n_samples: Number of samples to extract.
        random_state: Seed for reproducibility.
        
    Returns:
        A dataframe containing the sample users.
    """
    logger.info(f"Extracting {n_samples} sample users...")
    
    # Try to get a mix of positive and negative target examples if possible
    if "y" in df.columns:
        # Stratified sampling based on target
        try:
            samples = df.groupby("y", group_keys=False).apply(
                lambda x: x.sample(min(len(x), max(1, n_samples // 2)), random_state=random_state)
            )
            # If we didn't get exactly n_samples, sample the rest randomly
            if len(samples) < n_samples:
                remaining = n_samples - len(samples)
                additional = df.drop(samples.index).sample(remaining, random_state=random_state)
                samples = pd.concat([samples, additional])
            elif len(samples) > n_samples:
                samples = samples.sample(n_samples, random_state=random_state)
        except Exception as e:
            logger.warning(f"Stratified sampling failed: {e}. Falling back to random sampling.")
            samples = df.sample(n_samples, random_state=random_state)
    else:
        samples = df.sample(n_samples, random_state=random_state)
        
    # Add a synthetic user_id for demo purposes
    samples = samples.copy()
    samples.insert(0, "user_id", [f"demo_user_{i:03d}" for i in range(1, len(samples) + 1)])
    
    logger.info("Sample users extracted.")
    return samples

def save_sample_users(df: pd.DataFrame, output_path: str | Path) -> None:
    """Save the sample users to a JSON file for easy frontend consumption."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as records
    records = df.to_dict(orient="records")
    
    import json
    with open(path, "w") as f:
        json.dump(records, f, indent=2)
        
    logger.info(f"Sample users saved to {path}")
