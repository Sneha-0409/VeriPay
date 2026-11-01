from backend.app.config.thresholds import (
    FRAUD_THRESHOLD,
    RECIPIENT_MATCH_THRESHOLD
)


CONTEXT_WARN_THRESHOLD = 0.30
CONTEXT_BLOCK_THRESHOLD = 0.65


def assess_risk(
    fraud_probability: float | None = None,
    context_score: float | None = None,
    recipient_match_confidence: float | None = None
) -> dict:
    """
    Evaluate available fraud-model and contextual risk assessments.

    None means that an assessment was not performed.
    It does not mean zero risk.
    """

    if fraud_probability is not None:
        if not 0.0 <= fraud_probability <= 1.0:
            raise ValueError(
                "Fraud probability must be between 0 and 1."
            )

    if context_score is not None:
        if not 0.0 <= context_score <= 1.0:
            raise ValueError(
                "Context score must be between 0 and 1."
            )
    if recipient_match_confidence is not None:
        if not 0.0 <= recipient_match_confidence <= 1.0:
            raise ValueError(
                "recipient_match_confidence must be between 0 and 1"
            )
    if fraud_probability is None and context_score is None:
        raise ValueError(
            "At least one risk assessment must be provided."
        )
    # 1. High ML fraud probability.
    if (
        fraud_probability is not None
        and fraud_probability >= FRAUD_THRESHOLD
    ):
        return {
            "risk_level": "HIGH",
            "decision": "BLOCK",
            "reason": (
                "The fraud-model probability meets or exceeds "
                "the configured blocking threshold."
            ),
        }

    # 2. High contextual risk.
    if (
        context_score is not None
        and context_score >= CONTEXT_BLOCK_THRESHOLD
    ):
        return {
            "risk_level": "HIGH",
            "decision": "BLOCK",
            "reason": (
                "Contextual risk is high. Verify the recipient "
                "and payment details before proceeding."
            ),
        }
    if (
        recipient_match_confidence is not None
        and recipient_match_confidence < RECIPIENT_MATCH_THRESHOLD
    ):
        return {
            "risk_level": "REVIEW",
            "decision": "REQUEST_CLARIFICATION",
            "reason": (
                "Recipient match confidence is too low. "
                "Please confirm the intended recipient."
            )
        }

    # 3. Moderate contextual risk.
    if (
        context_score is not None
        and context_score >= CONTEXT_WARN_THRESHOLD
    ):
        return {
            "risk_level": "MEDIUM",
            "decision": "WARN",
            "reason": (
                "Contextual risk is elevated. Verify the payment "
                "details before proceeding."
            ),
        }

    # 4. ML-only assessment.
    if context_score is None:
        if fraud_probability is not None:
            return {
                "risk_level": "LOW",
                "decision": "PROCEED",
                "reason": (
                    "Fraud-model probability is below the blocking "
                    "threshold. Contextual risk was not evaluated."
                ),
            }

        return {
            "risk_level": "REVIEW",
            "decision": "WARN",
            "reason": "No contextual assessment is available.",
        }

    # 5. Context-only assessment.
    if fraud_probability is None:
        return {
            "risk_level": "LOW",
            "decision": "PROCEED",
            "reason": (
                "Contextual risk is below the warning threshold. "
                "The fraud model was not evaluated."
            ),
        }

    # 6. Both assessments are available and below thresholds.
    return {
        "risk_level": "LOW",
        "decision": "PROCEED",
        "reason": (
            "Both fraud-model and contextual risk are below "
            "their configured warning thresholds."
        ),
    }
