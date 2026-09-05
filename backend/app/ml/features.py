import pandas as pd


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts candidate features for the XGBoost model.
    """
    features = pd.DataFrame()

    # 1. Continuous / Numerical
    features["amount"] = df.get("amount", 0.0)
    features["past_attempts"] = df.get("past_attempts", 0)

    # 2. Categoricals encoded simply
    error_codes = [
        "timeout_or_gateway_error", "insufficient_funds", "lost_card",
        "stolen_card", "do_not_honor", "fraud_suspected", "R01_nsf",
        "R02_account_closed", "R03_no_account", "generic_decline", "unknown"
    ]
    for code in error_codes:
        features[f"err_{code}"] = (df.get("error_code") == code).astype(int)

    payment_methods = ["card", "ach", "wallet"]
    for method in payment_methods:
        features[f"pm_{method}"] = (
            df.get("payment_method") == method).astype(int)

    return features


def get_feature_list():
    df_dummy = pd.DataFrame({"amount": [0.0], "past_attempts": [
                            0], "error_code": [""], "payment_method": [""]})
    return extract_features(df_dummy).columns.tolist()
