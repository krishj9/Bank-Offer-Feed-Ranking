# Serverless Lambda assets

Used by **Option B** in [docs/install-aws.md](../../../docs/install-aws.md).

Build from the repository root (after local pipelines and training):

```bash
docker build -f infra/aws/serverless/Dockerfile -t bofr-api .
```

Requires `ml/artifacts/baseline_model.joblib`, `data/processed/sample_users.json`, and `data/synthetic/offers.csv` to exist before `docker build`.
