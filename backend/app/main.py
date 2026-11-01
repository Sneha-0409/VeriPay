# from fastapi import FastAPI, HTTPException, UploadFile, File
# from fastapi.middleware.cors import CORSMiddleware

# from backend.app.config.thresholds import FRAUD_THRESHOLD
# from backend.app.logger import logger
# from backend.app.risk.decision import assess_risk
# from backend.app.risk.model import predict_fraud_probability
# from backend.app.risk.features import (
#     PaymentContext,
#     extract_context_features,
# )
# from backend.app.risk.scorer import score_payment_context
# from backend.app.schemas import (
#     ContextPredictionRequest,
#     PaymentContextRequest,
# )
# from backend.app.voice.transcription import transcribe_audio


# app = FastAPI(
#     title="VeriPay CPDE API",
#     version="0.4.0",
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",
#         "http://localhost:5174",
#         "http://127.0.0.1:5173",
#         "http://127.0.0.1:5174",
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# logger.info("IEEE-CIS Random Forest model loaded successfully")


# @app.get("/health")
# def health():
#     return {"status": "ok"}


# def build_payment_context(data: PaymentContextRequest) -> PaymentContext:
#     return PaymentContext(
#         recipient_is_known=data.recipient_is_known,
#         amount=data.amount,
#         typical_amount=data.typical_amount,
#         recipient_match_confidence=data.recipient_match_confidence,
#         voice_intent_confidence=data.voice_intent_confidence,
#     )


# @app.post("/predict")
# def predict(data: list[float | None]):
#     try:
#         probability = predict_fraud_probability(data)
#         risk = assess_risk(fraud_probability=probability)

#         logger.info(
#             "ML prediction completed | probability=%.4f | decision=%s",
#             probability,
#             risk["decision"],
#         )

#         return {
#             "prediction": int(probability >= FRAUD_THRESHOLD),
#             "fraud_probability": probability,
#             "threshold": FRAUD_THRESHOLD,
#             "risk_level": risk["risk_level"],
#             "decision": risk["decision"],
#             "reason": risk["reason"],
#             "model_status": "EVALUATED",
#             "payment_execution": "NOT_EXECUTED",
#         }

#     except (TypeError, ValueError) as exc:
#         raise HTTPException(status_code=422, detail=str(exc))
#     except Exception:
#         logger.exception("Prediction failed")
#         raise HTTPException(
#             status_code=500,
#             detail="Prediction failed. Check the backend logs.",
#         )


# @app.post("/assess-context")
# def assess_context(data: PaymentContextRequest):
#     """
#     Assess voice-payment context without invoking the IEEE-CIS model.
#     """

#     try:
#         context = build_payment_context(data)

#         context_features = extract_context_features(context)
#         context_result = score_payment_context(context_features)

#         risk = assess_risk(
#             fraud_probability=None,
#             context_score=context_result["context_score"],
#         )

#         payment_decision = (
#             "BLOCK"
#             if risk["decision"] == "BLOCK"
#             else "AWAITING_CONFIRMATION"
#         )

#         logger.info(
#             "Context assessment completed | score=%.4f | decision=%s",
#             context_result["context_score"],
#             risk["decision"],
#         )

#         return {
#             "assessment_type": "CONTEXT_ONLY",
#             "fraud_model_status": "NOT_EVALUATED",
#             "fraud_probability": None,
#             "context_score": context_result["context_score"],
#             "context_risk_level": context_result["context_risk_level"],
#             "context_signals": context_result["context_signals"],
#             "scoring_weights": context_result["scoring_weights"],
#             "risk_level": risk["risk_level"],
#             "risk_decision": risk["decision"],
#             "reason": risk["reason"],
#             "payment_decision": payment_decision,
#             "confirmation_required": payment_decision != "BLOCK",
#             "payment_execution": "NOT_EXECUTED",
#         }

#     except (TypeError, ValueError) as exc:
#         raise HTTPException(status_code=422, detail=str(exc))
#     except Exception:
#         logger.exception("Context assessment failed")
#         raise HTTPException(
#             status_code=500,
#             detail="Context assessment failed. Check the backend logs.",
#         )


# @app.post("/predict-context")
# def predict_context(data: ContextPredictionRequest):
#     """
#     Combined IEEE-CIS fraud-model and contextual assessment.
#     """

#     try:
#         fraud_probability = predict_fraud_probability(
#             data.transaction_features
#         )

#         context = build_payment_context(data.context)

#         context_features = extract_context_features(context)
#         context_result = score_payment_context(context_features)

#         risk = assess_risk(
#             fraud_probability=fraud_probability,
#             context_score=context_result["context_score"],
#         )

#         payment_decision = (
#             "BLOCK"
#             if risk["decision"] == "BLOCK"
#             else "AWAITING_CONFIRMATION"
#         )

#         return {
#             "assessment_type": "HYBRID",
#             "fraud_model_status": "EVALUATED",
#             "fraud_probability": fraud_probability,
#             "fraud_threshold": FRAUD_THRESHOLD,
#             "context_score": context_result["context_score"],
#             "context_risk_level": context_result["context_risk_level"],
#             "context_signals": context_result["context_signals"],
#             "scoring_weights": context_result["scoring_weights"],
#             "risk_level": risk["risk_level"],
#             "risk_decision": risk["decision"],
#             "reason": risk["reason"],
#             "payment_decision": payment_decision,
#             "confirmation_required": payment_decision != "BLOCK",
#             "payment_execution": "NOT_EXECUTED",
#         }

#     except (TypeError, ValueError) as exc:
#         raise HTTPException(status_code=422, detail=str(exc))
#     except Exception:
#         logger.exception("Hybrid prediction failed")
#         raise HTTPException(
#             status_code=500,
#             detail="Hybrid prediction failed. Check the backend logs.",
#         )


# @app.post("/transcribe")
# async def transcribe(file: UploadFile = File(...)):
#     try:
#         if file.content_type not in (
#             "audio/wav",
#             "audio/x-wav",
#             "audio/wave",
#             "application/octet-stream",
#         ):
#             raise HTTPException(
#                 status_code=415,
#                 detail="Please upload a WAV audio file.",
#             )

#         audio_bytes = await file.read()

#         if not audio_bytes:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Uploaded audio file is empty.",
#             )

#         if len(audio_bytes) > 10 * 1024 * 1024:
#             raise HTTPException(
#                 status_code=413,
#                 detail="Audio file must be smaller than 10 MB.",
#             )

#         transcript = transcribe_audio(audio_bytes)

#         logger.info("Voice transcription completed successfully")

#         return {
#             "transcript": transcript,
#             "status": "TRANSCRIBED",
#             "payment_execution": "NOT_EXECUTED",
#         }

#     except HTTPException:
#         raise
#     except ValueError as exc:
#         raise HTTPException(status_code=422, detail=str(exc))
#     except Exception:
#         logger.exception("Voice transcription endpoint failed")
#         raise HTTPException(
#             status_code=500,
#             detail="Voice transcription failed.",
#         )
#     finally:
#         await file.close()



from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config.thresholds import FRAUD_THRESHOLD
from backend.app.logger import logger
from backend.app.risk.decision import assess_risk
from backend.app.risk.model import predict_fraud_probability
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
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
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
    """Build context for the existing hybrid assessment."""

    return PaymentContext(
        recipient_is_known=data.recipient_is_known,
        amount=data.amount,
        typical_amount=data.typical_amount,
        recipient_match_confidence=data.recipient_match_confidence,
        voice_intent_confidence=data.voice_intent_confidence,
    )


def get_payment_decision(risk):
    decision = risk["decision"]

    if decision == "BLOCK":
        return "BLOCK"

    if decision == "REQUEST_CLARIFICATION":
        return "REQUEST_CLARIFICATION"

    return "AWAITING_CONFIRMATION"


@app.post("/predict")
def predict(data: list[float | None]):
    """Run the standalone IEEE-CIS fraud model."""

    try:
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
            detail="Prediction failed. Check backend logs.",
        )


@app.post("/assess-context")
def assess_context(data: ContextAssessmentRequest):
    """
    Assess payment context using backend-managed recipient history.
    The IEEE-CIS model is not invoked by this endpoint.
    """

    try:
        profile = get_recipient_profile(data.recipient_name)

        recipient_found = profile["found"]
        history_available = profile["history_available"]

        recipient = profile["recipient"]

        recipient_is_known = (
            recipient_found
            and recipient["verified_by_user"]
            and recipient["is_active"]
        )

        # Use the historical median only when sufficient history exists.
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
        )

        context_features = extract_context_features(context)
        context_result = score_payment_context(context_features)

        risk = assess_risk(
            fraud_probability=None,
            context_score=context_result["context_score"],
            recipient_match_confidence=data.recipient_match_confidence
        )

        # Unknown recipients or insufficient history require review.
        manual_verification_required = (
            not recipient_is_known or not history_available
        )

        if (
            manual_verification_required
            and risk["decision"] != "REQUEST_CLARIFICATION"
        ):
            risk = {
                "risk_level": "REVIEW",
                "decision": "WARN",
                "reason": (
                    "Recipient identity or transaction history could "
                    "not be sufficiently verified. Please review the "
                    "recipient and payment details."
                ),
            }

        payment_decision = get_payment_decision(risk)

        if not recipient_found:
            recipient_status = "NOT_IN_SAVED_CONTACTS"
        elif not recipient["is_active"]:
            recipient_status = "INACTIVE"
        elif not recipient["verified_by_user"]:
            recipient_status = "NOT_VERIFIED"
        else:
            recipient_status = "KNOWN_VERIFIED_RECIPIENT"

        logger.info(
            "Context assessment | recipient=%s | score=%.4f | decision=%s",
            data.recipient_name,
            context_result["context_score"],
            risk["decision"],
        )

        return {
            "assessment_type": "CONTEXT_ONLY",
            "fraud_model_status": "NOT_EVALUATED",
            "fraud_probability": None,

            "recipient": {
                "requested_name": data.recipient_name,
                "status": recipient_status,
                "profile": recipient,
                "successful_transaction_count": profile["transaction_count"],
                "last_paid": profile["last_paid"],
                "history_available": history_available,
            },

            "payment": {
                "amount": data.amount,
                "historical_typical_amount": typical_amount,
                "amount_baseline_available": history_available,
            },

            "context_score": context_result["context_score"],
            "context_risk_level": context_result["context_risk_level"],
            "context_signals": context_result["context_signals"],
            "scoring_weights": context_result["scoring_weights"],

            "risk_level": risk["risk_level"],
            "risk_decision": risk["decision"],
            "reason": risk["reason"],

            "manual_verification_required": manual_verification_required,
            "payment_decision": payment_decision,
            "confirmation_required": payment_decision == "AWAITING_CONFIRMATION",
            "payment_execution": "NOT_EXECUTED",
        }

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
    """Run combined IEEE-CIS and contextual assessment."""

    try:
        fraud_probability = predict_fraud_probability(
            data.transaction_features
        )

        context = build_payment_context(data.context)
        context_features = extract_context_features(context)
        context_result = score_payment_context(context_features)

        risk = assess_risk(
            fraud_probability=fraud_probability,
            context_score=context_result["context_score"],
            recipient_match_confidence=data.context.recipient_match_confidence
        )

        payment_decision = get_payment_decision(risk)

        return {
            "assessment_type": "HYBRID",
            "fraud_model_status": "EVALUATED",
            "fraud_probability": fraud_probability,
            "fraud_threshold": FRAUD_THRESHOLD,
            "context_score": context_result["context_score"],
            "context_risk_level": context_result["context_risk_level"],
            "context_signals": context_result["context_signals"],
            "scoring_weights": context_result["scoring_weights"],
            "risk_level": risk["risk_level"],
            "risk_decision": risk["decision"],
            "reason": risk["reason"],
            "payment_decision": payment_decision,
            "confirmation_required": payment_decision == "AWAITING_CONFIRMATION",
            "payment_execution": "NOT_EXECUTED",
        }

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
    """Transcribe a voice command, extract payment intent, and assess context."""

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

        # Step 1: Speech-to-text
        transcript = transcribe_audio(audio_bytes)

        # Step 2: Extract payment intent
        intent = extract_payment_intent(transcript)

        if intent["intent"] != "PAYMENT" or intent["requires_clarification"]:
            return {
                "status": "CLARIFICATION_REQUIRED",
                "transcript": transcript,
                "intent": intent,
                "reason": "Payment details are incomplete or unclear.",
                "payment_execution": "NOT_EXECUTED",
            }

        # Step 3: Resolve recipient against saved contacts
        profile = get_recipient_profile(intent["recipient_name"])

        if not profile["found"]:
            return {
                "status": "CLARIFICATION_REQUIRED",
                "transcript": transcript,
                "intent": intent,
                "reason": (
                    "Recipient could not be uniquely matched "
                    "to a saved contact."
                ),
                "payment_execution": "NOT_EXECUTED",
            }

        recipient = profile["recipient"]

        # Do not assess or proceed with inactive/unverified recipients.
        if not recipient["is_active"] or not recipient["verified_by_user"]:
            return {
                "status": "VERIFICATION_REQUIRED",
                "transcript": transcript,
                "intent": intent,
                "recipient": recipient,
                "reason": "Recipient requires verification.",
                "payment_execution": "NOT_EXECUTED",
            }

        # Step 4: Run the existing context assessment.
        # These confidence values are provisional demo assumptions,
        # not confidence scores produced by Whisper.
        assessment = assess_context(
            ContextAssessmentRequest(
                recipient_name=recipient["name"],
                amount=intent["amount"],
                recipient_match_confidence=0.95,
                voice_intent_confidence=0.95,
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
