"""
Trains two models on the cleaned historical F1 dataset (2000-2024):

1. podium_clf  -> GradientBoostingClassifier predicting P(Top 3 Finish)
2. points_reg  -> GradientBoostingRegressor predicting points scored in a race

Both use only information that is known BEFORE a race is run (grid position,
season-to-date form, circuit characteristics), so the same feature pipeline
can be reused later for forward season simulation.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score, roc_auc_score, mean_absolute_error, r2_score, log_loss
)
from sklearn.model_selection import train_test_split

from data_prep import FEATURE_COLUMNS, TARGET_POINTS, TARGET_PODIUM, DATA_DIR

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


def time_based_split(df, test_years=(2023, 2024)):
    train = df[~df["year"].isin(test_years)]
    test = df[df["year"].isin(test_years)]
    return train, test


def main():
    df = pd.read_csv(DATA_DIR / "race_data_clean.csv")

    train, test = time_based_split(df)
    Xtr, Xte = train[FEATURE_COLUMNS], test[FEATURE_COLUMNS]

    # ---- Podium classifier ----
    ytr_c, yte_c = train[TARGET_PODIUM], test[TARGET_PODIUM]
    clf = GradientBoostingClassifier(
        n_estimators=300, max_depth=3, learning_rate=0.05,
        subsample=0.8, random_state=42
    )
    clf.fit(Xtr, ytr_c)
    proba = clf.predict_proba(Xte)[:, 1]
    pred = clf.predict(Xte)
    clf_metrics = {
        "accuracy": round(accuracy_score(yte_c, pred), 4),
        "roc_auc": round(roc_auc_score(yte_c, proba), 4),
        "log_loss": round(log_loss(yte_c, proba), 4),
    }
    print("Podium classifier metrics (test = 2023-2024):", clf_metrics)

    # ---- Points regressor ----
    ytr_r, yte_r = train[TARGET_POINTS], test[TARGET_POINTS]
    reg = GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.8, random_state=42
    )
    reg.fit(Xtr, ytr_r)
    pred_r = reg.predict(Xte)
    pred_r = np.clip(pred_r, 0, None)
    reg_metrics = {
        "mae": round(mean_absolute_error(yte_r, pred_r), 4),
        "r2": round(r2_score(yte_r, pred_r), 4),
    }
    print("Points regressor metrics (test = 2023-2024):", reg_metrics)

    # Refit on ALL data for the final deployed model (more signal for simulation)
    clf_full = GradientBoostingClassifier(
        n_estimators=300, max_depth=3, learning_rate=0.05,
        subsample=0.8, random_state=42
    ).fit(df[FEATURE_COLUMNS], df[TARGET_PODIUM])

    reg_full = GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.8, random_state=42
    ).fit(df[FEATURE_COLUMNS], df[TARGET_POINTS])

    joblib.dump(clf_full, MODELS_DIR / "podium_clf.joblib")
    joblib.dump(reg_full, MODELS_DIR / "points_reg.joblib")

    feat_importance = {
        "podium_clf": dict(zip(FEATURE_COLUMNS, clf_full.feature_importances_.round(4).tolist())),
        "points_reg": dict(zip(FEATURE_COLUMNS, reg_full.feature_importances_.round(4).tolist())),
    }
    metrics = {
        "podium_clf": clf_metrics,
        "points_reg": reg_metrics,
        "feature_importance": feat_importance,
        "n_train_rows": int(len(df)),
        "features": FEATURE_COLUMNS,
    }
    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("Saved models + metrics to", MODELS_DIR)


if __name__ == "__main__":
    main()
