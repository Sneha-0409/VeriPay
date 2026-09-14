from backend.app.config.thresholds import FRAUD_THRESHOLD

def assess_risk(fraud_probability: float):
    if fraud_probability >= FRAUD_THRESHOLD:
        return {
            "risk_level": "HIGH",
            "decision": "BLOCK"
        }
    return {
        "risk_level": "LOW",
        "decision": "PROCEED"
    }