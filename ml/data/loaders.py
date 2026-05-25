import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

def load_raw_bank_data(file_path: str | Path) -> pd.DataFrame:
    """
    Load the raw bank-additional-full.csv dataset.
    
    Args:
        file_path: Path to the raw CSV file.
        
    Returns:
        pd.DataFrame containing the loaded data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found at {path}")
        
    logger.info(f"Loading raw data from {path}")
    
    # The UCI bank dataset uses semicolons as separators
    df = pd.read_csv(path, sep=";")
    
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
    logger.info(f"Columns: {list(df.columns)}")
    
    return df
