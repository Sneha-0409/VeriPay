
# import re


# PAYMENT_ACTIONS = (
#     "send",
#     "pay",
#     "transfer",
# )


# def normalize_transcript(transcript: str) -> str:
#     """Normalize common Whisper transcription variations."""

#     text = transcript.strip().lower()

#     # Correct a few observed/context-specific ASR errors.
#     text = re.sub(r"^\s*saan\b", "send", text)
#     text = re.sub(r"\b2\b(?=\s+[a-z])", "to", text)

#     return re.sub(r"\s+", " ", text).strip()


# def extract_payment_intent(transcript: str) -> dict:
#     """
#     Extract payment action, amount and recipient from a transcript.

#     This is a rule-based prototype parser, not an ML intent classifier.
#     Uncertain or incomplete details require clarification.
#     """

#     if not transcript or not transcript.strip():
#         return {
#             "intent": "UNKNOWN",
#             "recipient_name": None,
#             "amount": None,
#             "missing_fields": ["recipient", "amount"],
#             "requires_clarification": True,
#             "normalized_transcript": "",
#         }

#     normalized = normalize_transcript(transcript)

#     # Verify that the user is expressing a payment action.
#     action_found = any(
#         re.search(rf"\b{action}\b", normalized)
#         for action in PAYMENT_ACTIONS
#     )

#     if not action_found:
#         return {
#             "intent": "UNKNOWN",
#             "recipient_name": None,
#             "amount": None,
#             "missing_fields": ["payment_intent"],
#             "requires_clarification": True,
#             "normalized_transcript": normalized,
#         }

#     # Extract a numeric payment amount.
#     amount_match = re.search(
#         r"\b(?:rs\.?|inr|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)"
#         r"\s*(?:rupees?|rs\.?|inr)?\b",
#         normalized,
#     )

#     amount = None

#     if amount_match:
#         amount = float(amount_match.group(1).replace(",", ""))

#         if amount <= 0:
#             amount = None

#     # Extract the recipient following "to".
#     recipient_match = re.search(
#         r"\bto\s+([a-z]+(?:\s+[a-z]+){0,2})",
#         normalized,
#     )

#     # Also support formats such as:
#     # "pay Rahul 500 rupees" and "pay Rahul".
#     if not recipient_match:
#         recipient_match = re.search(
#             r"\b(?:pay|send|transfer)\s+"
#             r"([a-z]+(?:\s+[a-z]+){0,2})"
#             r"(?=\s|$)",
#             normalized,
#         )

#     if recipient_match:
#         candidate = recipient_match.group(1).strip()

#         # Do not treat amount words as recipient names.
#         if candidate in {"rupees", "rs", "inr"}:
#             recipient_match = None

#     recipient_name = None

#     if recipient_match:
#         recipient_name = recipient_match.group(1).strip().title()

#     missing_fields = []

#     if not recipient_name:
#         missing_fields.append("recipient")

#     if amount is None:
#         missing_fields.append("amount")

#     return {
#         "intent": "PAYMENT",
#         "recipient_name": recipient_name,
#         "amount": amount,
#         "missing_fields": missing_fields,
#         "requires_clarification": len(missing_fields) > 0,
#         "normalized_transcript": normalized,
#     }

import re


PAYMENT_ACTIONS = (
    "send",
    "pay",
    "transfer",
)

URGENCY_WORDS = {
    "immediately",
    "urgent",
    "urgently",
    "quickly",
    "right",
    "now",
    "asap",
    "fast",
}

RECIPIENT_STOP_WORDS = {
    "immediately",
    "urgent",
    "urgently",
    "quickly",
    "now",
    "asap",
    "fast",
    "rupee",
    "rupees",
    "rs",
    "inr",
    "to",
    "send",
    "pay",
    "transfer",
}


def normalize_transcript(transcript: str) -> str:
    """Normalize common Whisper transcription variations."""

    text = transcript.strip().lower()

    # Correct observed/context-specific ASR errors.
    text = re.sub(r"^\s*saan\b", "send", text)
    text = re.sub(r"\b2\b(?=\s+[a-z])", "to", text)

    return re.sub(r"\s+", " ", text).strip()


def extract_payment_intent(transcript: str) -> dict:
    """
    Extract payment action, amount, recipient, and urgency.

    This is a rule-based prototype parser, not an ML intent classifier.
    Uncertain or incomplete details require clarification.
    """

    if not transcript or not transcript.strip():
        return {
            "intent": "UNKNOWN",
            "recipient_name": None,
            "amount": None,
            "urgency_detected": False,
            "missing_fields": ["recipient", "amount"],
            "requires_clarification": True,
            "normalized_transcript": "",
        }

    normalized = normalize_transcript(transcript)

    # ---------------------------------------------------------
    # 1. Detect payment action
    # ---------------------------------------------------------

    action_found = any(
        re.search(rf"\b{action}\b", normalized)
        for action in PAYMENT_ACTIONS
    )

    if not action_found:
        return {
            "intent": "UNKNOWN",
            "recipient_name": None,
            "amount": None,
            "urgency_detected": False,
            "missing_fields": ["payment_intent"],
            "requires_clarification": True,
            "normalized_transcript": normalized,
        }

    # ---------------------------------------------------------
    # 2. Detect urgency independently
    # ---------------------------------------------------------

    urgency_detected = any(
        re.search(rf"\b{word}\b", normalized)
        for word in URGENCY_WORDS
    )

    # ---------------------------------------------------------
    # 3. Extract numeric amount
    # ---------------------------------------------------------

    amount_match = re.search(
        r"\b(?:rs\.?|inr|rupees?)?\s*"
        r"(\d+(?:,\d{3})*(?:\.\d+)?)"
        r"\s*(?:rupees?|rs\.?|inr)?\b",
        normalized,
    )

    amount = None

    if amount_match:
        try:
            amount = float(amount_match.group(1).replace(",", ""))

            if amount <= 0:
                amount = None

        except ValueError:
            amount = None

    # ---------------------------------------------------------
    # 4. Remove payment action, amount, currency and urgency
    #    before extracting recipient
    # ---------------------------------------------------------

    recipient_text = normalized

    if amount_match:
        recipient_text = (
            recipient_text[:amount_match.start()]
            + " "
            + recipient_text[amount_match.end():]
        )

    # Remove currency tokens and urgency phrases.
    recipient_text = re.sub(
        r"\b(?:rupees?|rs\.?|inr)\b",
        " ",
        recipient_text,
    )

    recipient_text = re.sub(
        r"\bright\s+now\b",
        " ",
        recipient_text,
    )

    for word in URGENCY_WORDS:
        recipient_text = re.sub(
            rf"\b{re.escape(word)}\b",
            " ",
            recipient_text,
        )

    recipient_text = re.sub(r"\s+", " ", recipient_text).strip()

    # ---------------------------------------------------------
    # 5. Extract recipient following "to"
    # ---------------------------------------------------------

    recipient_match = re.search(
        r"\bto\s+(.+)",
        recipient_text,
    )

    candidate = None

    if recipient_match:
        candidate = recipient_match.group(1).strip()

    else:
        # Support: "Pay Rahul Sharma 500 rupees"
        action_match = re.search(
            r"\b(?:pay|send|transfer)\s+(.+)",
            recipient_text,
        )

        if action_match:
            candidate = action_match.group(1).strip()

    # ---------------------------------------------------------
    # 6. Clean candidate recipient
    # ---------------------------------------------------------

    recipient_name = None

    if candidate:
        words = candidate.split()

        cleaned_words = []

        for word in words:

            if word in RECIPIENT_STOP_WORDS:
                break

            if not re.fullmatch(r"[a-z]+", word):
                break

            cleaned_words.append(word)

            # Prototype supports up to three name tokens.
            if len(cleaned_words) >= 3:
                break

        if cleaned_words:
            recipient_name = " ".join(cleaned_words).title()

    # ---------------------------------------------------------
    # 7. Validate extracted fields
    # ---------------------------------------------------------

    missing_fields = []

    if not recipient_name:
        missing_fields.append("recipient")

    if amount is None:
        missing_fields.append("amount")

    # ---------------------------------------------------------
    # 8. Return parsed intent
    # ---------------------------------------------------------

    return {
        "intent": "PAYMENT",
        "recipient_name": recipient_name,
        "amount": amount,
        "urgency_detected": urgency_detected,
        "missing_fields": missing_fields,
        "requires_clarification": len(missing_fields) > 0,
        "normalized_transcript": normalized,
    }