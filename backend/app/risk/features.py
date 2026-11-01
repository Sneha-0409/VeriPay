
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

#     if context.amount < 0 or context.typical_amount < 0:
#         raise ValueError("Payment amounts cannot be negative.")

#     if not 0.0 <= context.recipient_match_confidence <= 1.0:
#         raise ValueError("Recipient match confidence must be between 0 and 1.")

#     if not 0.0 <= context.voice_intent_confidence <= 1.0:
#         raise ValueError("Voice intent confidence must be between 0 and 1.")

#     if context.typical_amount > 0:
#         amount_ratio = context.amount / context.typical_amount
#     else:
#         amount_ratio = 1.0 if context.amount == 0 else 2.0

#     return {
#         "recipient_novelty": int(not context.recipient_is_known),
#         "amount_ratio": float(amount_ratio),
#         "recipient_ambiguity": float(1.0 - context.recipient_match_confidence),
#         "voice_intent_uncertainty": float(1.0 - context.voice_intent_confidence),
#     }


from dataclasses import dataclass


@dataclass
class PaymentContext:
    recipient_is_known: bool
    amount: float
    typical_amount: float
    recipient_match_confidence: float
    voice_intent_confidence: float


def extract_context_features(context: PaymentContext) -> dict:
    """Extract normalized contextual signals for the CPDE."""

    if context.amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    if context.typical_amount < 0:
        raise ValueError("Typical payment amount cannot be negative.")

    if not 0.0 <= context.recipient_match_confidence <= 1.0:
        raise ValueError(
            "Recipient match confidence must be between 0 and 1."
        )

    if not 0.0 <= context.voice_intent_confidence <= 1.0:
        raise ValueError(
            "Voice intent confidence must be between 0 and 1."
        )

    if context.typical_amount > 0:
        amount_ratio = context.amount / context.typical_amount
    else:
        # No historical baseline is available.
        # Do not pretend that a reliable amount comparison exists.
        amount_ratio = 1.0

    return {
        "recipient_novelty": float(not context.recipient_is_known),
        "amount_ratio": float(amount_ratio),
        "recipient_ambiguity": (
            1.0 - context.recipient_match_confidence
        ),
        "voice_intent_uncertainty": (
            1.0 - context.voice_intent_confidence
        ),
    }
