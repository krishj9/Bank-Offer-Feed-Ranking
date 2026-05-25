"""AWS Lambda entrypoint: exposes FastAPI via Mangum (HTTP API / Function URL)."""

from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="off")
