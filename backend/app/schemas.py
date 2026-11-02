
# from pydantic import BaseModel, Field, ConfigDict


# class PaymentContextRequest(BaseModel):
#     """Context inputs used by the existing hybrid assessment."""

#     recipient_is_known: bool
#     amount: float = Field(gt=0)
#     typical_amount: float = Field(ge=0)
#     recipient_match_confidence: float = Field(ge=0, le=1)
#     voice_intent_confidence: float = Field(ge=0, le=1)


# class ContextAssessmentRequest(BaseModel):
#     """Inputs for backend-managed, context-only payment assessment."""

#     model_config = ConfigDict(str_strip_whitespace=True)

#     recipient_name: str = Field(min_length=1, max_length=100)
#     amount: float = Field(gt=0)
#     recipient_match_confidence: float = Field(ge=0, le=1)
#     voice_intent_confidence: float = Field(ge=0, le=1)


# class ContextPredictionRequest(BaseModel):
#     """Combined IEEE-CIS and contextual assessment request."""

#     transaction_features: list[float | None] = Field(
#         min_length=23,
#         max_length=23,
#         description=(
#             "The 23 IEEE-CIS features in the model's training order. "
#             "Missing values are imputed using training medians."
#         ),
#     )

#     context: PaymentContextRequest


from pydantic import BaseModel, Field, ConfigDict


class PaymentContextRequest(BaseModel):
    """Inputs for the six-signal CPDE hybrid assessment."""

    recipient_is_known: bool
    amount: float = Field(gt=0)
    typical_amount: float = Field(ge=0)
    recipient_match_confidence: float = Field(ge=0, le=1)
    voice_intent_confidence: float = Field(ge=0, le=1)

    urgency_detected: bool = False
    unusual_time: bool = False
    repeated_failures: bool = False


class ContextAssessmentRequest(BaseModel):
    """Inputs for backend-managed, context-only payment assessment."""

    model_config = ConfigDict(str_strip_whitespace=True)

    recipient_name: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    recipient_match_confidence: float = Field(ge=0, le=1)
    voice_intent_confidence: float = Field(ge=0, le=1)

    urgency_detected: bool = False
    unusual_time: bool = False
    repeated_failures: bool = False


class ContextPredictionRequest(BaseModel):
    """Combined IEEE-CIS and contextual assessment request."""

    transaction_features: list[float | None] = Field(
        min_length=23,
        max_length=23,
        description=(
            "The 23 IEEE-CIS features in the model's training order. "
            "Missing values are imputed using training medians."
        ),
    )

    context: PaymentContextRequest
