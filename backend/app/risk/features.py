# from dataclasses import dataclass


# @dataclass
# class PaymentContext:
#     recipient_is_known: bool
#     amount: float
#     typical_amount: float
#     recipient_match_confidence: float
#     voice_intent_confidence: float


# def extract_context_features(context: PaymentContext) -> dict:
#     """Extract normalized contextual signals for the CPDE."""

#     if context.amount <= 0:
#         raise ValueError("Payment amount must be greater than zero.")

#     if context.typical_amount < 0:
#         raise ValueError("Typical payment amount cannot be negative.")

#     if not 0.0 <= context.recipient_match_confidence <= 1.0:
#         raise ValueError(
#             "Recipient match confidence must be between 0 and 1."
#         )

#     if not 0.0 <= context.voice_intent_confidence <= 1.0:
#         raise ValueError(
#             "Voice intent confidence must be between 0 and 1."
#         )

#     if context.typical_amount > 0:
#         amount_ratio = context.amount / context.typical_amount
#     else:
#         # No historical baseline is available.
#         # Do not pretend that a reliable amount comparison exists.
#         amount_ratio = 1.0

#     return {
#         "recipient_novelty": float(not context.recipient_is_known),
#         "amount_ratio": float(amount_ratio),
#         "recipient_ambiguity": (
#             1.0 - context.recipient_match_confidence
#         ),
#         "voice_intent_uncertainty": (
#             1.0 - context.voice_intent_confidence
#         ),
#     }


from dataclasses import dataclass


@dataclass
class PaymentContext:
    recipient_is_known: bool
    amount: float
    typical_amount: float
    recipient_match_confidence: float
    voice_intent_confidence: float

    # Additional signals used by the notebook's six-signal CPDE
    fraud_probability: float = 0.0
    recipient_match_count: int = 1
    urgency_detected: bool = False
    unusual_time: bool = False
    repeated_failures: bool = False
    is_payment: bool = True


def extract_context_features(context: PaymentContext) -> dict:
    """Extract inputs for the six-signal CPDE."""

    if context.amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    if context.typical_amount < 0:
        raise ValueError("Typical payment amount cannot be negative.")

    if not 0.0 <= context.recipient_match_confidence <= 1.0:
        raise ValueError("Recipient match confidence must be between 0 and 1.")

    if not 0.0 <= context.voice_intent_confidence <= 1.0:
        raise ValueError("Voice intent confidence must be between 0 and 1.")

    if not 0.0 <= context.fraud_probability <= 1.0:
        raise ValueError("Fraud probability must be between 0 and 1.")

    if context.recipient_match_count < 0:
        raise ValueError("Recipient match count cannot be negative.")

    amount_deviation = (
        min(1.0, max(0.0, (context.amount / context.typical_amount - 1) / 4))
        if context.typical_amount > 0
        else (1.0 if context.amount > 0 else 0.0)
    )

    return {
        "intent_confidence": context.voice_intent_confidence,
        "fraud_probability": context.fraud_probability,
        "amount_deviation": amount_deviation,
        "is_new_recipient": not context.recipient_is_known,
        "recipient_match_count": context.recipient_match_count,
        "urgency_detected": context.urgency_detected,
        "unusual_time": context.unusual_time,
        "repeated_failures": context.repeated_failures,
        "is_payment": context.is_payment,
    }
