
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

ZERO_FEATURES = [0] * 23


def make_request(context):
    return {
        "transaction_features": ZERO_FEATURES,
        "context": context,
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_moderate_context_requires_confirmation():
    response = client.post(
        "/predict-context",
        json=make_request({
            "recipient_is_known": False,
            "amount": 5000,
            "typical_amount": 1000,
            "recipient_match_confidence": 1.0,
            "voice_intent_confidence": 0.95,
        }),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["payment_decision"] == "AWAITING_CONFIRMATION"
    assert data["confirmation_required"] is True
    assert data["payment_execution"] == "NOT_EXECUTED"


def test_high_context_risk_blocks_payment():
    response = client.post(
        "/predict-context",
        json=make_request({
            "recipient_is_known": False,
            "amount": 5000,
            "typical_amount": 1000,
            "recipient_match_confidence": 0.0,
            "voice_intent_confidence": 0.0,
        }),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["context_score"] == 1.0
    assert data["risk_level"] == "HIGH"
    assert data["risk_decision"] == "BLOCK"
    assert data["payment_decision"] == "BLOCK"
    assert data["payment_execution"] == "NOT_EXECUTED"


def test_invalid_feature_count_is_rejected():
    response = client.post(
        "/predict-context",
        json={
            "transaction_features": [0] * 22,
            "context": {
                "recipient_is_known": True,
                "amount": 500,
                "typical_amount": 1000,
                "recipient_match_confidence": 1.0,
                "voice_intent_confidence": 0.95,
            },
        },
    )

    assert response.status_code == 422


def test_all_responses_never_execute_payments():
    for context in [
        {
            "recipient_is_known": True,
            "amount": 500,
            "typical_amount": 1000,
            "recipient_match_confidence": 1.0,
            "voice_intent_confidence": 0.95,
        },
        {
            "recipient_is_known": False,
            "amount": 5000,
            "typical_amount": 1000,
            "recipient_match_confidence": 0.0,
            "voice_intent_confidence": 0.0,
        },
    ]:
        response = client.post(
            "/predict-context",
            json=make_request(context),
        )

        assert response.status_code == 200
        assert response.json()["payment_execution"] == "NOT_EXECUTED"

def test_ambiguous_recipient_requests_clarification():
    response = client.post(
        "/predict-context",
        json=make_request({
            "recipient_is_known": True,
            "amount": 500,
            "typical_amount": 1000,
            "recipient_match_confidence": 0.10,
            "voice_intent_confidence": 0.95,
        }),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["risk_decision"] == "REQUEST_CLARIFICATION"
    assert data["payment_decision"] == "REQUEST_CLARIFICATION"
    assert data["confirmation_required"] is False
    assert data["payment_execution"] == "NOT_EXECUTED"

def test_low_risk_transaction_proceeds_to_confirmation():
    response = client.post(
        "/predict-context",
        json=make_request({
            "recipient_is_known": True,
            "amount": 500,
            "typical_amount": 500,
            "recipient_match_confidence": 0.95,
            "voice_intent_confidence": 0.95,
        }),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["risk_decision"] == "PROCEED"
    assert data["payment_decision"] == "AWAITING_CONFIRMATION"
    assert data["confirmation_required"] is True
    assert data["payment_execution"] == "NOT_EXECUTED"

def test_elevated_context_risk_warns_and_requires_confirmation():
    response = client.post(
        "/predict-context",
        json=make_request({
            "recipient_is_known": True,
            "amount": 50000,
            "typical_amount": 500,
            "recipient_match_confidence": 0.95,
            "voice_intent_confidence": 0.95,
        }),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["risk_level"] == "MEDIUM"
    assert data["risk_decision"] == "WARN"
    assert data["payment_decision"] == "AWAITING_CONFIRMATION"
    assert data["confirmation_required"] is True
    assert data["payment_execution"] == "NOT_EXECUTED"