from app.ml.features import extract_features, get_feature_list
import json
import xgboost as xgb
from sklearn.metrics import roc_auc_score, log_loss
import pandas as pd
from pathlib import Path
import sys

# Ensure backend module path is available
sys.path.append(str(Path(__file__).resolve().parent.parent))


def train_and_evaluate():
    data_dir = Path("data/output")
    model_dir = Path("app/ml/models")
    model_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    dev_df = pd.read_csv(data_dir / "development.csv")
    val_df = pd.read_csv(data_dir / "validation.csv")

    # 2. Extract features
    X_train = extract_features(dev_df)
    y_train = dev_df["recoverable"].astype(int)

    X_val = extract_features(val_df)
    y_val = val_df["recoverable"].astype(int)

    # 3. Train model
    print("Training XGBoost model...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42
    )
    model.fit(X_train, y_train)

    # 4. Evaluate on validation
    preds_proba = model.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, preds_proba)
    loss = log_loss(y_val, preds_proba)

    # 5. Save model and metadata
    model_version = "v1.0"
    model_path = model_dir / f"xgb_recovery_{model_version}.json"
    model.save_model(model_path)

    metadata = {
        "model_version": model_version,
        "feature_list": get_feature_list(),
        "training_split_metadata": {
            "dev_size": len(dev_df),
            "val_size": len(val_df)
        },
        "validation_metrics": {
            "roc_auc": auc,
            "log_loss": loss
        },
        "model_artifact_path": str(model_path)
    }

    with open(model_dir / f"metadata_{model_version}.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("\nTraining complete.")
    print(f"Validation AUC: {auc:.4f}")
    print(f"Validation Log Loss: {loss:.4f}")
    print(f"Model saved to {model_path}")
    print(f"Metadata saved to {model_dir / f'metadata_{model_version}.json'}")


if __name__ == "__main__":
    train_and_evaluate()
