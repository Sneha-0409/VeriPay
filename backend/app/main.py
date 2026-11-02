from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config.thresholds import FRAUD_THRESHOLD
from backend.app.logger import logger
from backend.app.risk.decision import assess_risk
from backend.app.risk.features import (
    PaymentContext,
    extract_context_features,
)
from backend.app.risk.scorer import score_payment_context
from backend.app.risk.profile_store import get_recipient_profile
from backend.app.schemas import (
    ContextAssessmentRequest,
    ContextPredictionRequest,
    PaymentContextRequest,
)
from backend.app.voice.transcription import transcribe_audio
from backend.app.voice.intent_extraction import extract_payment_intent


app = FastAPI(
    title="VeriPay CPDE API",
    version="0.6.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://veripay-secure-pay.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logger.info("VeriPay API initialized")


@app.get("/health")
def health():
    return {"status": "ok"}


def build_payment_context(data: PaymentContextRequest) -> PaymentContext:
    """Build the context inputs for the six-signal CPDE."""

    return PaymentContext(
        recipient_is_known=data.recipient_is_known,
        amount=data.amount,
        typical_amount=data.typical_amount,
        recipient_match_confidence=data.recipient_match_confidence,
        voice_intent_confidence=data.voice_intent_confidence,
        urgency_detected=data.urgency_detected,
        unusual_time=data.unusual_time,
        repeated_failures=data.repeated_failures,
    )


def build_cpde_response(
    context_result: dict,
    assessment_type: str,
    fraud_probability=None,
    fraud_model_status="NOT_EVALUATED",
    extra_fields=None,
) -> dict:
    """Map the CPDE result to the response fields used by the frontend."""

    decision = context_result["decision"]
    risk_score = context_result["risk_score"]
    risk_level = context_result["risk_level"]
    reasons = context_result["reasons"]

    if decision == "BLOCK":
        payment_decision = "BLOCK"
    elif decision == "CLARIFY":
        payment_decision = "CLARIFICATION_REQUIRED"
    elif decision == "ALLOW":
        payment_decision = "ALLOW"
    else:
        payment_decision = "AWAITING_CONFIRMATION"

    response = {
        "assessment_type": assessment_type,
        "fraud_model_status": fraud_model_status,
        "fraud_probability": fraud_probability,
        "context_score": risk_score,
        "context_risk_level": risk_level,
        "context_signals": context_result["risk_signals"],
        "scoring_weights": context_result["scoring_weights"],
        "risk_level": risk_level,
        "risk_decision": decision,
        "decision": decision,
        "reason": " ".join(reasons),
        "payment_decision": payment_decision,
        "confirmation_required": payment_decision == "AWAITING_CONFIRMATION",
        "payment_execution": "NOT_EXECUTED",
    }

    if extra_fields:
        response.update(extra_fields)

    return response


@app.post("/predict")
def predict(data: list[float | None]):
    """Run the standalone IEEE-CIS fraud model."""

    try:
        # Lazy import prevents loading the large model during API startup.
        from backend.app.risk.model import predict_fraud_probability

        probability = predict_fraud_probability(data)
        risk = assess_risk(fraud_probability=probability)

        logger.info(
            "ML prediction completed | probability=%.4f | decision=%s",
            probability,
            risk["decision"],
        )

        return {
            "assessment_type": "ML_ONLY",
            "prediction": int(probability >= FRAUD_THRESHOLD),
            "fraud_probability": probability,
            "threshold": FRAUD_THRESHOLD,
            "risk_level": risk["risk_level"],
            "decision": risk["decision"],
            "reason": risk["reason"],
            "model_status": "EVALUATED",
            "payment_execution": "NOT_EXECUTED",
        }

    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check the backend logs.",
        )


@app.post("/assess-context")
def assess_context(data: ContextAssessmentRequest):
    """Assess payment context using backend-managed recipient history."""

    try:
        profile = get_recipient_profile(data.recipient_name)

        recipient_found = profile["found"]
        recipient = profile["recipient"]
        history_available = profile["history_available"]

        recipient_is_known = (
            recipient_found
            and recipient["verified_by_user"]
            and recipient["is_active"]
        )

        typical_amount = (
            profile["typical_amount"]
            if history_available
            else 0.0
        )

        context = PaymentContext(
            recipient_is_known=recipient_is_known,
            amount=data.amount,
            typical_amount=typical_amount,
            recipient_match_confidence=data.recipient_match_confidence,
            voice_intent_confidence=data.voice_intent_confidence,
            fraud_probability=0.0,
            recipient_match_count=profile["match_count"],
            urgency_detected=data.urgency_detected,
            unusual_time=data.unusual_time,
            repeated_failures=data.repeated_failures,
        )

        context_features = extract_context_features(context)
        context_result = score_payment_context(context_features)

        manual_verification_required = (
            not recipient_is_known or not history_available
        )

        if not recipient_found:
            recipient_status = "NOT_IN_SAVED_CONTACTS"
        elif not recipient["is_active"]:
            recipient_status = "INACTIVE"
        elif not recipient["verified_by_user"]:
            recipient_status = "NOT_VERIFIED"
        else:
            recipient_status = "KNOWN_VERIFIED_RECIPIENT"

        logger.info(
            "Context assessment | recipient=%s | score=%s | decision=%s",
            data.recipient_name,
            context_result["risk_score"],
            context_result["decision"],
        )

        return build_cpde_response(
            context_result=context_result,
            assessment_type="CONTEXT_ONLY",
            fraud_probability=None,
            fraud_model_status="NOT_EVALUATED",
            extra_fields={
                "recipient": {
                    "requested_name": data.recipient_name,
                    "status": recipient_status,
                    "profile": recipient,
                    "match_count": profile["match_count"],
                    "successful_transaction_count": profile["transaction_count"],
                    "last_paid": profile["last_paid"],
                    "history_available": history_available,
                },
                "payment": {
                    "amount": data.amount,
                    "historical_typical_amount": typical_amount,
                    "amount_baseline_available": history_available,
                },
                "manual_verification_required": manual_verification_required,
            },
        )

    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Context assessment failed")
        raise HTTPException(
            status_code=500,
            detail="Context assessment failed. Check backend logs.",
        )


@app.post("/predict-context")
def predict_context(data: ContextPredictionRequest):
    """Run the IEEE-CIS model and the notebook's six-signal CPDE."""

    try:
        # Load the large fraud model only when this endpoint is called.
        from backend.app.risk.model import predict_fraud_probability

        fraud_probability = predict_fraud_probability(
            data.transaction_features
        )

        context = build_payment_context(data.context)
        context_features = extract_context_features(context)
        context_result = score_payment_context(context_features)

        logger.info(
            "Hybrid CPDE assessment | fraud_probability=%.4f | "
            "context_score=%s | decision=%s",
            fraud_probability,
            context_result["risk_score"],
            context_result["decision"],
        )

        return build_cpde_response(
            context_result=context_result,
            assessment_type="HYBRID",
            fraud_probability=fraud_probability,
            fraud_model_status="EVALUATED",
            extra_fields={
                "fraud_threshold": FRAUD_THRESHOLD,
            },
        )

    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Hybrid prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Hybrid prediction failed. Check backend logs.",
        )


@app.post("/voice-payment")
async def voice_payment(file: UploadFile = File(...)):
    """Transcribe a voice command, extract intent, and assess context."""

    try:
        if file.content_type not in (
            "audio/wav",
            "audio/x-wav",
            "audio/wave",
            "application/octet-stream",
        ):
            raise HTTPException(
                status_code=415,
                detail="Please upload a WAV audio file.",
            )

        audio_bytes = await file.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded audio file is empty.",
            )

        if len(audio_bytes) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Audio file must be smaller than 10 MB.",
            )

        transcript = transcribe_audio(audio_bytes)
        intent = extract_payment_intent(transcript)

        if (
            intent["intent"] != "PAYMENT"
            or intent["requires_clarification"]
        ):
            return {
                "status": "CLARIFICATION_REQUIRED",
                "transcript": transcript,
                "intent": intent,
                "reason": "Payment details are incomplete or unclear.",
                "payment_execution": "NOT_EXECUTED",
            }

        profile = get_recipient_profile(intent["recipient_name"])

        if not profile["found"]:
        # Multiple contacts match: ask the user to choose.
            if profile["match_count"] > 1:
                return {
                    "status": "RECIPIENT_SELECTION_REQUIRED",
                    "transcript": transcript,
                    "intent": intent,
                    "recipient_match_count": profile["match_count"],
                    "candidate_recipients": profile["candidate_recipients"],
                    "reason": profile["clarification_message"],
                    "payment_execution": "NOT_EXECUTED",
                }
        # No matching contact found.
            return {
                "status": "RECIPIENT_NOT_FOUND",
                "transcript": transcript,
                "intent": intent,
                "recipient_match_count": 0,
                "candidate_recipients": [],
                "reason": "No saved contact matched the requested recipient.",
                "payment_execution": "NOT_EXECUTED",
            }

        recipient = profile["recipient"]


        if not recipient["is_active"] or not recipient["verified_by_user"]:
            return {
                 "status": "VERIFICATION_REQUIRED",
                 "transcript": transcript,
                 "intent": intent,
                 "recipient": recipient,
                 "reason": "Recipient requires verification.",
                 "payment_execution": "NOT_EXECUTED",
             }

        # Provisional demo confidence values.
        # These are not confidence scores produced by Whisper.
        assessment = assess_context(
        ContextAssessmentRequest(
            recipient_name=recipient["name"],
            amount=intent["amount"],
            recipient_match_confidence=0.95,
            voice_intent_confidence=0.95,
            urgency_detected=intent["urgency_detected"],
        )
    )

        return {
            "status": "ASSESSMENT_COMPLETED",
            "transcript": transcript,
            "intent": intent,
            "assessment": assessment,
            "payment_execution": "NOT_EXECUTED",
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Voice payment assessment failed")
        raise HTTPException(
            status_code=500,
            detail="Voice payment assessment failed. Check backend logs.",
        )
    finally:
        await file.close()


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Transcribe a WAV audio recording."""

    try:
        if file.content_type not in (
            "audio/wav",
            "audio/x-wav",
            "audio/wave",
            "application/octet-stream",
        ):
            raise HTTPException(
                status_code=415,
                detail="Please upload a WAV audio file.",
            )

        audio_bytes = await file.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded audio file is empty.",
            )

        if len(audio_bytes) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Audio file must be smaller than 10 MB.",
            )

        transcript = transcribe_audio(audio_bytes)

        logger.info("Voice transcription completed successfully")

        return {
            "transcript": transcript,
            "status": "TRANSCRIBED",
            "payment_execution": "NOT_EXECUTED",
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Voice transcription endpoint failed")
        raise HTTPException(
            status_code=500,
            detail="Voice transcription failed.",
        )
    finally:
        await file.close()
