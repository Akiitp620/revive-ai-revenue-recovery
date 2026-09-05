import pytest
import pandas as pd
from app.ml.features import extract_features, get_feature_list
from app.ml.inference import RecoveryModel


def test_feature_extraction():
    data = [{
        "amount": 100.0,
        "past_attempts": 2,
        "error_code": "insufficient_funds",
        "payment_method": "card"
    }]
    df = pd.DataFrame(data)
    features = extract_features(df)

    assert features.iloc[0]["amount"] == 100.0
    assert features.iloc[0]["past_attempts"] == 2
    assert features.iloc[0]["err_insufficient_funds"] == 1
    assert features.iloc[0]["pm_card"] == 1

    # Verify shape matches global feature list
    assert list(features.columns) == get_feature_list()


def test_inference_module():
    try:
        model = RecoveryModel("v1.0")
    except FileNotFoundError:
        pytest.skip("Model not trained yet")

    event = {
        "amount": 150.0,
        "past_attempts": 1,
        "error_code": "timeout_or_gateway_error",
        "payment_method": "card"
    }

    prob = model.predict_probability(event)
    assert 0.0 <= prob <= 1.0
