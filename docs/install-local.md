# Local Installation Guide

This guide provides step-by-step instructions to set up the Bank Offer Feed Ranking application locally. It covers data preparation, ML training, running the backend, running the frontend, and executing tests.

## 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **uv** (recommended) or `venv`
- **Raw Dataset**: Download `bank-additional-full.csv` from the UCI Bank Marketing dataset and place it at `data/raw/bank-additional-full.csv`.

## 2. Clone and Setup
Clone the repository and navigate into the root directory:
```bash
git clone <repo_url>
cd BankOfferFeedRanking
```

## 3. Install Dependencies

### Python Dependencies
Using `uv` (recommended):
```bash
uv sync --extra dev
```

Alternatively, using `venv`:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

## 4. Run Data Pipelines
From the repository root, run the data preparation pipelines.
```bash
# Preprocess the raw dataset
uv run python -m ml.data.preprocess

# Generate synthetic offers and labels
uv run python -m ml.data.run_synthetic
```

## 5. ML Training (Optional)
To train the baseline ML model and generate offline evaluation metrics:
```bash
# Train the model and save artifacts to ml/artifacts/
uv run python -m ml.training.train

# Evaluate offline metrics
uv run python -m ml.evaluation.evaluate
```

## 6. Start the Backend
Start the FastAPI backend server. Run this from the `backend/` directory or root:
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
cd ..
```

## 7. Start the Frontend
In a new terminal window, start the React frontend:
```bash
cd frontend
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## 8. Verify the Setup
- **Backend Health:** `curl http://localhost:8000/health`
- **Sample Users API:** `curl http://localhost:8000/api/v1/sample-users`
- **Frontend UI:** Open your browser to `http://localhost:5173` (or the URL shown by Vite).

## 9. Run Quality Gate
Run all linting, type-checking, and tests (both backend and frontend) using the provided script:
```bash
bash scripts/quality.sh
```

## 10. Common Failure Modes
- **Dataset Missing:** Ensure `bank-additional-full.csv` is correctly placed in `data/raw/`.
- **Missing Artifacts:** If the backend fails to rank, verify that ML training completed and `baseline_model.joblib` exists in `ml/artifacts/`. The API has a fallback, but performance will degrade.
- **Port Conflicts:** If port 8000 is in use, start uvicorn on a different port and update the frontend `VITE_API_BASE_URL` accordingly.
- **Missing `duration` errors:** The `duration` feature from the UCI dataset is explicitly excluded by design to prevent data leakage. If custom code references it, errors will occur.
