
import re


PAYMENT_ACTIONS = (
    "send",
    "pay",
    "transfer",
)


def normalize_transcript(transcript: str) -> str:
    """Normalize common Whisper transcription variations."""

    text = transcript.strip().lower()

    # Correct a few observed/context-specific ASR errors.
    text = re.sub(r"^\s*saan\b", "send", text)
    text = re.sub(r"\b2\b(?=\s+[a-z])", "to", text)

    return re.sub(r"\s+", " ", text).strip()


def extract_payment_intent(transcript: str) -> dict:
    """
    Extract payment action, amount and recipient from a transcript.

    This is a rule-based prototype parser, not an ML intent classifier.
    Uncertain or incomplete details require clarification.
    """

    if not transcript or not transcript.strip():
        return {
            "intent": "UNKNOWN",
            "recipient_name": None,
            "amount": None,
            "missing_fields": ["recipient", "amount"],
            "requires_clarification": True,
            "normalized_transcript": "",
        }

    normalized = normalize_transcript(transcript)

    # Verify that the user is expressing a payment action.
    action_found = any(
        re.search(rf"\b{action}\b", normalized)
        for action in PAYMENT_ACTIONS
    )

    if not action_found:
        return {
            "intent": "UNKNOWN",
            "recipient_name": None,
            "amount": None,
            "missing_fields": ["payment_intent"],
            "requires_clarification": True,
            "normalized_transcript": normalized,
        }

    # Extract a numeric payment amount.
    amount_match = re.search(
        r"\b(?:rs\.?|inr|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)"
        r"\s*(?:rupees?|rs\.?|inr)?\b",
        normalized,
    )

    amount = None

    if amount_match:
        amount = float(amount_match.group(1).replace(",", ""))

        if amount <= 0:
            amount = None

    # Extract the recipient following "to".
    recipient_match = re.search(
        r"\bto\s+([a-z]+(?:\s+[a-z]+){0,2})",
        normalized,
    )

    # Also support formats such as:
    # "pay Rahul 500 rupees" and "pay Rahul".
    if not recipient_match:
        recipient_match = re.search(
            r"\b(?:pay|send|transfer)\s+"
            r"([a-z]+(?:\s+[a-z]+){0,2})"
            r"(?=\s|$)",
            normalized,
        )

    if recipient_match:
        candidate = recipient_match.group(1).strip()

        # Do not treat amount words as recipient names.
        if candidate in {"rupees", "rs", "inr"}:
            recipient_match = None

    recipient_name = None

    if recipient_match:
        recipient_name = recipient_match.group(1).strip().title()

    missing_fields = []

    if not recipient_name:
        missing_fields.append("recipient")

    if amount is None:
        missing_fields.append("amount")

    return {
        "intent": "PAYMENT",
        "recipient_name": recipient_name,
        "amount": amount,
        "missing_fields": missing_fields,
        "requires_clarification": len(missing_fields) > 0,
        "normalized_transcript": normalized,
    }
