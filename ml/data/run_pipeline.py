import logging
from pathlib import Path

from ml.data.loaders import load_raw_bank_data
from ml.data.validation import load_schema_contract, validate_raw_data, generate_validation_summary
from ml.data.preprocess import preprocess_data, save_processed_data, generate_preprocessing_summary
from ml.data.sample_users import extract_sample_users, save_sample_users

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_pipeline():
    base_dir = Path(__file__).parent.parent.parent
    raw_data_path = base_dir / "data" / "raw" / "bank-additional-full.csv"
    schema_path = base_dir / "shared" / "contracts" / "bank_data_schema.json"
    
    processed_data_path = base_dir / "data" / "processed" / "bank_processed.parquet"
    sample_users_path = base_dir / "data" / "processed" / "sample_users.json"
    
    validation_summary_path = base_dir / "output" / "reports" / "validation_summary.json"
    preprocessing_summary_path = base_dir / "output" / "reports" / "preprocessing_summary.json"
    
    logger.info("Starting data pipeline...")
    
    # 1. Load schema
    schema_contract = load_schema_contract(schema_path)
    
    # 2. Load raw data
    raw_df = load_raw_bank_data(raw_data_path)
    
    # 3. Validate raw data
    validate_raw_data(raw_df, schema_contract)
    generate_validation_summary(raw_df, validation_summary_path)
    
    # 4. Preprocess data
    processed_df = preprocess_data(raw_df, schema_contract)
    save_processed_data(processed_df, processed_data_path)
    generate_preprocessing_summary(processed_df, preprocessing_summary_path)
    
    # 5. Extract sample users
    sample_users_df = extract_sample_users(processed_df, n_samples=10)
    save_sample_users(sample_users_df, sample_users_path)
    
    logger.info("Data pipeline completed successfully.")

if __name__ == "__main__":
    run_pipeline()
