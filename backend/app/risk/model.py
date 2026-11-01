import json
import pickle
from pathlib import Path

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BACKEND_DIR / "models" / "ieee_cis_rf_model.pkl"
PREPROCESSING_PATH = (
    BACKEND_DIR / "models" / "ieee_cis_preprocessing.json"
)

with PREPROCESSING_PATH.open("r", encoding="utf-8") as file:
    PREPROCESSING = json.load(file)

FEATURE_NAMES = PREPROCESSING["features"]
FEATURE_MEDIANS = PREPROCESSING["medians"]

if len(FEATURE_NAMES) != 23:
    raise ValueError("Expected exactly 23 IEEE-CIS features.")

if len(FEATURE_MEDIANS) != 23:
    raise ValueError("Expected exactly 23 training medians.")

if FEATURE_NAMES != list(FEATURE_MEDIANS.keys()):
    raise ValueError("Feature order and median order do not match.")

with MODEL_PATH.open("rb") as file:
    rf_model = pickle.load(file)


if getattr(rf_model, "n_features_in_", None) != len(FEATURE_NAMES):
    raise ValueError("Model feature count does not match metadata.")


def prepare_transaction_features(features):

    if isinstance(features, dict):
        missing = [
            name for name in FEATURE_NAMES
            if name not in features
        ]

        extra = [
            name for name in features
            if name not in FEATURE_NAMES
        ]

        if missing or extra:
            raise ValueError(
                f"Feature mismatch. Missing: {missing}; Extra: {extra}"
            )

        values = [features[name] for name in FEATURE_NAMES]

    else:
        values = list(features)

    if len(values) != len(FEATURE_NAMES):
        raise ValueError(
            f"Expected {len(FEATURE_NAMES)} features, "
            f"received {len(values)}."
        )

    cleaned = {}

    for name, value in zip(FEATURE_NAMES, values):
        if value is None:
            cleaned[name] = FEATURE_MEDIANS[name]
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid numeric value for {name}."
            )

        if not pd.notna(numeric_value):
            cleaned[name] = FEATURE_MEDIANS[name]
        else:
            cleaned[name] = numeric_value

    return pd.DataFrame(
        [[cleaned[name] for name in FEATURE_NAMES]],
        columns=FEATURE_NAMES,
    )


def predict_fraud_probability(features):

    prepared = prepare_transaction_features(features)

    probability = float(
        rf_model.predict_proba(prepared)[0][1]
    )

    return probability