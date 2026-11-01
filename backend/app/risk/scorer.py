
# from backend.app.config.weights import (
#     RECIPIENT_NOVELTY_WEIGHT,
#     AMOUNT_DEVIATION_WEIGHT,
#     CONTACT_AMBIGUITY_WEIGHT,
#     URGENCY_LANGUAGE_WEIGHT,
#     HIGH_AMOUNT_WEIGHT,
# )


# def score_payment_context(features: dict) -> dict:
#     """Calculate a prototype contextual risk score from 0 to 1."""

#     recipient_novelty = float(features["recipient_novelty"])
#     amount_ratio = float(features["amount_ratio"])
#     recipient_ambiguity = float(features["recipient_ambiguity"])
#     voice_uncertainty = float(features["voice_intent_uncertainty"])

#     # Normalize contextual signals to the range [0, 1].
#     amount_deviation = min(abs(amount_ratio - 1.0) / 4.0, 1.0)
#     high_amount = float(amount_ratio >= 3.0)

#     signals = {
#         "recipient_novelty": recipient_novelty,
#         "amount_deviation": amount_deviation,
#         "recipient_ambiguity": recipient_ambiguity,
#         "urgency_language": voice_uncertainty,
#         "high_amount": high_amount,
#     }

#     weights = {
#         "recipient_novelty": RECIPIENT_NOVELTY_WEIGHT,
#         "amount_deviation": AMOUNT_DEVIATION_WEIGHT,
#         "recipient_ambiguity": CONTACT_AMBIGUITY_WEIGHT,
#         "urgency_language": URGENCY_LANGUAGE_WEIGHT,
#         "high_amount": HIGH_AMOUNT_WEIGHT,
#     }

#     total_weight = sum(weights.values())
#     if total_weight <= 0:
#         raise ValueError("Context scoring weights must sum to a positive value.")

#     context_score = sum(
#         signals[name] * weights[name]
#         for name in signals
#     ) / total_weight

#     return {
#         "context_score": float(context_score),
#         "context_risk_level": (
#             "HIGH" if context_score >= 0.65
#             else "MEDIUM" if context_score >= 0.30
#             else "LOW"
#         ),
#         "context_signals": signals,
#     }


from backend.app.config.weights import (
    RECIPIENT_NOVELTY_WEIGHT,
    AMOUNT_DEVIATION_WEIGHT,
    CONTACT_AMBIGUITY_WEIGHT,
    URGENCY_LANGUAGE_WEIGHT,
    HIGH_AMOUNT_WEIGHT,
)


def score_payment_context(features: dict) -> dict:
    """Calculate an explainable contextual risk score from 0 to 1."""

    recipient_novelty = float(features["recipient_novelty"])
    amount_ratio = float(features["amount_ratio"])
    recipient_ambiguity = float(features["recipient_ambiguity"])
    voice_uncertainty = float(features["voice_intent_uncertainty"])

    signals = {
        "recipient_novelty": recipient_novelty,
        "amount_deviation": min(abs(amount_ratio - 1.0) / 4.0, 1.0),
        "recipient_ambiguity": recipient_ambiguity,
        "voice_intent_uncertainty": voice_uncertainty,
        "high_amount": float(amount_ratio >= 3.0),
    }

    weights = {
        "recipient_novelty": RECIPIENT_NOVELTY_WEIGHT,
        "amount_deviation": AMOUNT_DEVIATION_WEIGHT,
        "recipient_ambiguity": CONTACT_AMBIGUITY_WEIGHT,
        "voice_intent_uncertainty": URGENCY_LANGUAGE_WEIGHT,
        "high_amount": HIGH_AMOUNT_WEIGHT,
    }

    if any(not 0.0 <= value <= 1.0 for value in signals.values()):
        raise ValueError("All contextual signals must be between 0 and 1.")

    if any(weight < 0 for weight in weights.values()):
        raise ValueError("Context scoring weights cannot be negative.")

    total_weight = sum(weights.values())

    if total_weight <= 0:
        raise ValueError("Context scoring weights must sum to a positive value.")

    context_score = sum(
        signals[name] * weights[name]
        for name in signals
    ) / total_weight

    context_risk_level = (
        "HIGH" if context_score >= 0.65
        else "MEDIUM" if context_score >= 0.30
        else "LOW"
    )

    return {
        "context_score": float(context_score),
        "context_risk_level": context_risk_level,
        "context_signals": signals,
        "scoring_weights": weights,
    }
