from fastapi import FastAPI
from backend.app.config.thresholds import FRAUD_THRESHOLD
from backend.app.logger import logger
import pickle
import os
from backend.app.risk.decision import assess_risk


app = FastAPI(
    title="VeriPay CPDE API",
    version="0.1.0"
)
model_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "models",
    "ieee_cis_rf_model.pkl"
)
with open(model_path, "rb") as f:
    rf_model = pickle.load(f)

logger.info("IEEE-CIS Random Forest model loaded successfully")

@app.get("/health")
def health():
    logger.info("Health endpoint accessed")
    return {"status": "ok"}

@app.post("/predict")
def predict(data: list[float]):
    probability = rf_model.predict_proba([data])[0][1]

    prediction = int(probability >= FRAUD_THRESHOLD)

    risk = assess_risk(probability)

    return {
        "prediction": prediction,
        "fraud_probability": float(probability),
        "threshold": FRAUD_THRESHOLD,
        "risk_level": risk["risk_level"],
        "decision": risk["decision"]
    }

@app.post("/predict")
def predict(data: list[float]):
    probability = rf_model.predict_proba([data])[0][1]
    prediction = int(probability >= FRAUD_THRESHOLD)
    risk = assess_risk(probability)
    return {
        "prediction": prediction,
        "fraud_probabilty": float(probability),
        "threshold": FRAUD_THRESHOLD,
        "risl_level": risk["risk_level"]
    }
