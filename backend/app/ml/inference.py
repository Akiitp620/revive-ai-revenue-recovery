import xgboost as xgb
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from app.ml.features import extract_features


class RecoveryModel:
    def __init__(self, model_version: str = "v1.0"):
        self.model_version = model_version
        self.model = xgb.XGBClassifier()
        model_path = Path(__file__).parent / "models" / \
            f"xgb_recovery_{model_version}.json"

        if not model_path.exists():
            raise FileNotFoundError(f"Model {model_path} not found.")

        self.model.load_model(model_path)

    def predict_probability(self, event: Dict[str, Any]) -> float:
        """
        Predicts recovery probability for a single payment failure event.
        """
        # Convert single dict to DataFrame row
        df = pd.DataFrame([event])
        features = extract_features(df)

        # XGBoost predict_proba returns a 2D array of shape (n_samples, n_classes)
        # Class 1 is 'recoverable' == True
        proba = self.model.predict_proba(features)[0][1]
        return float(proba)
