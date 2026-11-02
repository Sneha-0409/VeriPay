# from backend.app.config.weights import (
#     RECIPIENT_NOVELTY_WEIGHT,
#     AMOUNT_DEVIATION_WEIGHT,
#     CONTACT_AMBIGUITY_WEIGHT,
#     URGENCY_LANGUAGE_WEIGHT,
#     HIGH_AMOUNT_WEIGHT,
# )


# def score_payment_context(features: dict) -> dict:
#     """Calculate an explainable contextual risk score from 0 to 1."""

#     recipient_novelty = float(features["recipient_novelty"])
#     amount_ratio = float(features["amount_ratio"])
#     recipient_ambiguity = float(features["recipient_ambiguity"])
#     voice_uncertainty = float(features["voice_intent_uncertainty"])

#     signals = {
#         "recipient_novelty": recipient_novelty,
#         "amount_deviation": min(abs(amount_ratio - 1.0) / 4.0, 1.0),
#         "recipient_ambiguity": recipient_ambiguity,
#         "voice_intent_uncertainty": voice_uncertainty,
#         "high_amount": float(amount_ratio >= 3.0),
#     }

#     weights = {
#         "recipient_novelty": RECIPIENT_NOVELTY_WEIGHT,
#         "amount_deviation": AMOUNT_DEVIATION_WEIGHT,
#         "recipient_ambiguity": CONTACT_AMBIGUITY_WEIGHT,
#         "voice_intent_uncertainty": URGENCY_LANGUAGE_WEIGHT,
#         "high_amount": HIGH_AMOUNT_WEIGHT,
#     }

#     if any(not 0.0 <= value <= 1.0 for value in signals.values()):
#         raise ValueError("All contextual signals must be between 0 and 1.")

#     if any(weight < 0 for weight in weights.values()):
#         raise ValueError("Context scoring weights cannot be negative.")

#     total_weight = sum(weights.values())

#     if total_weight <= 0:
#         raise ValueError("Context scoring weights must sum to a positive value.")

#     context_score = sum(
#         signals[name] * weights[name]
#         for name in signals
#     ) / total_weight

#     context_risk_level = (
#         "HIGH" if context_score >= 0.65
#         else "MEDIUM" if context_score >= 0.30
#         else "LOW"
#     )

#     return {
#         "context_score": float(context_score),
#         "context_risk_level": context_risk_level,
#         "context_signals": signals,
#         "scoring_weights": weights,
#     }


def score_payment_context(features: dict) -> dict:
    """Apply the six-signal CPDE decision policy from the research notebook."""

    intent_confidence = float(features["intent_confidence"])
    fraud_probability = float(features["fraud_probability"])
    amount_deviation = float(features["amount_deviation"])
    is_new_recipient = bool(features["is_new_recipient"])
    recipient_match_count = int(features["recipient_match_count"])
    urgency_detected = bool(features["urgency_detected"])
    unusual_time = bool(features["unusual_time"])
    repeated_failures = bool(features["repeated_failures"])
    is_payment = bool(features["is_payment"])

    for name, value in {
        "intent_confidence": intent_confidence,
        "fraud_probability": fraud_probability,
        "amount_deviation": amount_deviation,
    }.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0 and 1.")

    if intent_confidence < 0.55 or recipient_match_count != 1:
        reasons = []

        if intent_confidence < 0.55:
            reasons.append("Voice intent confidence is too low.")

        if recipient_match_count != 1:
            reasons.append("Recipient is missing or ambiguous.")

        return {
            "risk_score": None,
            "risk_level": "UNASSESSED",
            "decision": "CLARIFY",
            "risk_signals": {},
            "scoring_weights": {},
            "reasons": reasons,
        }

    signals = {
        "fraud_probability": fraud_probability,
        "amount_deviation": amount_deviation,
        "new_recipient": float(is_new_recipient),
        "urgency": float(urgency_detected),
        "unusual_time": float(unusual_time),
        "repeated_failures": float(repeated_failures),
    }

    weights = {
        "fraud_probability": 0.40,
        "amount_deviation": 0.20,
        "new_recipient": 0.15,
        "urgency": 0.10,
        "unusual_time": 0.05,
        "repeated_failures": 0.10,
    }

    risk_score = round(
        min(1.0, max(0.0, sum(
            signals[name] * weights[name] for name in signals
        ))),
        4,
    )

    reasons = [
        f"{name.replace('_', ' ').title()} contributes to transaction risk."
        for name, signal in signals.items()
        if signal > 0
    ]

    if risk_score >= 0.65:
        decision, risk_level = "BLOCK", "HIGH"
    elif risk_score >= 0.30:
        decision, risk_level = "CONFIRM", "MEDIUM"
    elif is_payment:
        decision, risk_level = "CONFIRM", "LOW"
        reasons.append("Explicit user confirmation is required before payment.")
    else:
        decision, risk_level = "ALLOW", "LOW"

    if not reasons:
        reasons.append("No configured risk signal was triggered.")

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "decision": decision,
        "risk_signals": signals,
        "scoring_weights": weights,
        "reasons": reasons,
    }
