from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import joblib
import numpy as np
import pandas as pd

from .features import FEATURES, latest_features

MODEL_DIR = Path("models")


@dataclass
class ProbabilityResult:
    probability: float
    raw_probability: float
    model_ready: bool
    model_version: str
    evidence: str
    expected_value_r: float
    risk_reward: float


class ProbabilityEngine:
    """Two independent probabilistic profiles: SCALP and SWING.

    Each profile is trained offline as an ensemble of logistic regression and
    histogram gradient boosting, then calibrated on a strictly later time slice.
    At runtime the engine only consumes the most recent feature row.
    """

    def __init__(self, model_dir: Path = MODEL_DIR):
        self.model_dir = model_dir
        self.models: dict[str, dict] = {}
        self._load("SCALP")
        self._load("SWING")

    def _load(self, mode: str) -> None:
        path = self.model_dir / f"{mode.lower()}_probability.joblib"
        if path.exists():
            try:
                self.models[mode] = joblib.load(path)
            except Exception:
                self.models.pop(mode, None)

    def ready(self, mode: str) -> bool:
        return mode.upper() in self.models

    def predict(self, df: pd.DataFrame, side: str, mode: str, risk_reward: float) -> ProbabilityResult:
        mode = mode.upper()
        row = latest_features(df, side)
        if row is None:
            return ProbabilityResult(0.5, 0.5, False, "no-features", "insufficient data", 0.0, risk_reward)

        if mode in self.models:
            pack = self.models[mode]
            x = pd.DataFrame([row[FEATURES].values], columns=FEATURES)
            probs = [float(pack["logistic"].predict_proba(x)[0, 1]), float(pack["boosting"].predict_proba(x)[0, 1])]
            raw = float(np.mean(probs))
            calibrated = float(pack["calibrator"].predict([[raw]])[0, 0])
            calibrated = min(max(calibrated, 0.01), 0.99)
            version = pack.get("version", "ensemble")
            evidence = pack.get("evidence", "trained")
            ready = True
        else:
            # Conservative fallback. It is deliberately NOT presented as a real probability.
            bullish = (
                row["ema20_gap"] > 0 and row["ema50_gap"] > 0 and row["macd_hist_pct"] > 0
                if side.upper() == "LONG"
                else row["ema20_gap"] < 0 and row["ema50_gap"] < 0 and row["macd_hist_pct"] < 0
            )
            raw = 0.58 if bullish else 0.42
            calibrated = raw
            version = "heuristic-fallback"
            evidence = "model not trained"
            ready = False

        ev = calibrated * risk_reward - (1.0 - calibrated)
        return ProbabilityResult(calibrated, raw, ready, version, evidence, ev, risk_reward)


engine = ProbabilityEngine()


def probability_confidence(probability: float, model_ready: bool) -> int:
    if not model_ready:
        return 50
    # Probability is evidence-backed; confidence is just a display score.
    return int(round(probability * 100))
