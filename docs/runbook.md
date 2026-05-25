# Developer Runbook

This guide covers local environment setup, ML training, inference execution, and UI startup.

## 1. Local Setup
1. **Clone the Repo:**
   ```bash
   git clone <repo_url>
   cd BankOfferFeedRanking
   ```
2. **Python Environment (Backend & ML):**
   Ensure Python 3.10+ and `uv` (or pip) are installed.
   ```bash
   uv sync
   # or
   pip install -r requirements.txt
   ```
3. **Node Environment (Frontend):**
   ```bash
   cd frontend
   npm install
   ```

## 2. Data Preparation & ML Training
1. **Raw Data:** Download `bank-additional-full.csv` from UCI and place it in `data/raw/`.
2. **Run Pipeline:**
   ```bash
   # Preprocess data
   uv run python -m ml.data.preprocess
   # Generate synthetic catalogs and pairs
   uv run python -m ml.data.run_synthetic
   # Train the model
   uv run python -m ml.training.train
   # Evaluate offline metrics
   uv run python -m ml.evaluation.evaluate
   ```
   *Artifacts (`baseline_model.joblib`) will be saved to `ml/artifacts/`.*

## 3. Inference Service (Backend)
Start the FastAPI server:
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```
- Health Check: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`

## 4. UI Startup (Frontend)
Start the React feed UI:
```bash
cd frontend
npm run dev
```
Access at `http://localhost:5173` (or the port defined by Vite/Next).

## 5. Testing
- **Backend/ML:**
  ```bash
  uv run pytest backend/tests ml/tests
  ```
- **Frontend:**
  ```bash
  cd frontend
  npm run test
  ```

## 6. Common Failure Modes
- **Missing `duration` errors:** If custom queries fail because `duration` is not found, remember it is strictly excluded from feature schemas by design.
- **Artifact Not Found:** If the backend fails to rank, ensure `ml.training.train` has been successfully run and artifacts exist in `ml/artifacts/`. The system has a fallback mode but will log warnings.
- **Port Conflicts:** If `8000` is busy, configure the backend port and update `.env` in the frontend to point to the new URL.