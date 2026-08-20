from fastapi import FastAPI
from app.logger import logger

app = FastAPI(
    title="VeriPay CPDE API",
    version="0.1.0"
)

@app.get("/health")
def health():
    logger.info("Health endpoint accessed")
    return {"status": "ok"}