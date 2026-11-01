from pathlib import Path
import pickle

from fastapi import FastAPI, HTTPException
from backend.app.config.thresholds import FRAUD_THRESHOLD
from backend.app.logger import logger
from backend.app.risk.decision import assess_risk

from backend.app.schemas import ContextPredictionRequest
from backend.app.risk.features import PaymentContext, extract_context_features
from backend.app.risk.scorer import score_payment_context

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

@app.post("/predict/context")
def predict_with_context(data: ContextPredictionRequest):
    try:
        # Step 1: Predict transaction fraud probability.
        probability = float(
            rf_model.predict_proba([data.transaction_features])[0][1]
        )

        # Step 2: Extract payment-context features.
        context = PaymentContext(
            recipient_is_known=data.context.recipient_is_known,
            amount=data.context.amount,
            typical_amount=data.context.typical_amount,
            recipient_match_confidence=data.context.recipient_match_confidence,
            voice_intent_confidence=data.context.voice_intent_confidence,
        )

        context_features = extract_context_features(context)

        # Step 3: Calculate contextual risk.
        context_result = score_payment_context(context_features)

        # Step 4: Combine transaction and contextual risk.
        risk = assess_risk(
            probability,
            context_score=context_result["context_score"],
        )

        logger.info(
            "Context prediction completed | fraud_probability=%.4f | "
            "context_score=%.4f | decision=%s",
            probability,
            context_result["context_score"],
            risk["decision"],
        )

        return {
            "prediction": int(probability >= FRAUD_THRESHOLD),
            "fraud_probability": probability,
            "threshold": FRAUD_THRESHOLD,
            "context_score": context_result["context_score"],
            "context_risk_level": context_result["context_risk_level"],
            "context_signals": context_result["context_signals"],
            "risk_level": risk["risk_level"],
            "decision": risk["decision"],
            "reason": risk["reason"],
        }

    except (TypeError, ValueError) as exc:
        logger.exception("Invalid context prediction input")
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Context prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Context prediction failed. Check the backend logs.",
        )