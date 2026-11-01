from pathlib import Path
import pickle

from fastapi import FastAPI, HTTPException
from backend.app.config.thresholds import FRAUD_THRESHOLD
from backend.app.logger import logger
from backend.app.risk.decision import assess_risk


app = FastAPI(
    title="VeriPay CPDE API",
    version="0.2.0",
)

MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "ieee_cis_rf_model.pkl"
)

with MODEL_PATH.open("rb") as f:
    rf_model = pickle.load(f)

logger.info("IEEE-CIS Random Forest model loaded successfully")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(data: list[float]):
    try:
        expected_features = getattr(rf_model, "n_features_in_", None)

        if expected_features is not None and len(data) != expected_features:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Expected {expected_features} features, "
                    f"but received {len(data)}."
                ),
            )

        probability = float(rf_model.predict_proba([data])[0][1])
        risk = assess_risk(probability)

        logger.info(
            "Prediction completed | probability=%.4f | decision=%s",
            probability,
            risk["decision"],
        )

        return {
            "prediction": int(probability >= FRAUD_THRESHOLD),
            "fraud_probability": probability,
            "threshold": FRAUD_THRESHOLD,
            "risk_level": risk["risk_level"],
            "decision": risk["decision"],
        }

    except HTTPException:
        raise
    except (TypeError, ValueError) as exc:
        logger.exception("Invalid prediction input")
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check the backend logs.",
        )
