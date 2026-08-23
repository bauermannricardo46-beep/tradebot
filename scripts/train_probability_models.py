from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import httpx
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from app.features import FEATURES, feature_frame

BINANCE = "https://api.binance.com/api/v3/klines"
MODE_CONFIG = {
    "SCALP": {"interval": "5m", "atr_mult": 1.0, "min_pct": 0.0025},
    "SWING": {"interval": "1h", "atr_mult": 1.8, "min_pct": 0.006},
}


async def fetch_history(symbol: str, interval: str, bars: int) -> pd.DataFrame:
    rows: list[list] = []
    end_time = None
    async with httpx.AsyncClient(timeout=20.0) as client:
        while len(rows) < bars:
            params = {"symbol": symbol, "interval": interval, "limit": min(1000, bars - len(rows))}
            if end_time is not None:
                params["endTime"] = end_time
            response = await client.get(BINANCE, params=params)
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            rows = batch + rows
            oldest = int(batch[0][0])
            end_time = oldest - 1
            if len(batch) < 1000:
                break
    rows = rows[-bars:]
    columns = ["open_time", "open", "high", "low", "close", "volume", "close_time", "qv", "trades", "tb", "tq", "ignore"]
    df = pd.DataFrame(rows, columns=columns)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df[["open_time", "open", "high", "low", "close", "volume"]].dropna().reset_index(drop=True)


def outcome_labels(df: pd.DataFrame, side: str, mode: str) -> pd.Series:
    cfg = MODE_CONFIG[mode]
    work = df.copy()
    tr = pd.concat([
        work["high"] - work["low"],
        (work["high"] - work["close"].shift()).abs(),
        (work["low"] - work["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    distance = np.maximum(atr * cfg["atr_mult"], work["close"] * cfg["min_pct"])
    labels = pd.Series(np.nan, index=work.index, dtype=float)

    # This look-ahead exists only to define a supervised training target.
    # It is NOT a maximum holding time for live trading.
    max_lookahead = min(500, max(100, len(work) // 4))
    for i in range(len(work) - max_lookahead):
        entry = float(work.loc[i, "close"])
        stop = entry - float(distance.iloc[i]) if side == "LONG" else entry + float(distance.iloc[i])
        target = entry + float(distance.iloc[i]) * 2 if side == "LONG" else entry - float(distance.iloc[i]) * 2
        for j in range(i + 1, min(len(work), i + 1 + max_lookahead)):
            hi = float(work.loc[j, "high"])
            lo = float(work.loc[j, "low"])
            if side == "LONG":
                hit_stop = lo <= stop
                hit_target = hi >= target
            else:
                hit_stop = hi >= stop
                hit_target = lo <= target
            if hit_stop and hit_target:
                # Conservative tie-break: assume stop was hit first.
                labels.iloc[i] = 0
                break
            if hit_target:
                labels.iloc[i] = 1
                break
            if hit_stop:
                labels.iloc[i] = 0
                break
    return labels


def make_dataset(df: pd.DataFrame, mode: str) -> tuple[pd.DataFrame, pd.Series]:
    frames = []
    labels = []
    for side in ("LONG", "SHORT"):
        x = feature_frame(df, side)
        y = outcome_labels(df, side, mode)
        joined = x.join(y.rename("target"), how="inner").dropna()
        if not joined.empty:
            frames.append(joined[FEATURES])
            labels.append(joined["target"].astype(int))
    return pd.concat(frames, ignore_index=True), pd.concat(labels, ignore_index=True)


def walk_forward_indices(n: int, folds: int = 9):
    fold = n // (folds + 1)
    for k in range(3, folds + 1):
        train_end = fold * k
        test_end = min(n, train_end + fold)
        if train_end > 100 and test_end > train_end:
            yield train_end, test_end


def train_mode(x: pd.DataFrame, y: pd.Series, mode: str, out_dir: Path) -> dict:
    if len(x) < 1500 or y.nunique() < 2:
        raise RuntimeError(f"{mode}: not enough labeled data ({len(x)} rows)")

    split = int(len(x) * 0.80)
    x_train, x_test = x.iloc[:split], x.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    logistic = Pipeline([
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=2000, class_weight="balanced")),
    ])
    boosting = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.04, max_leaf_nodes=15, random_state=42)
    logistic.fit(x_train, y_train)
    boosting.fit(x_train, y_train)

    p_log = logistic.predict_proba(x_test)[:, 1]
    p_boost = boosting.predict_proba(x_test)[:, 1]
    raw = (p_log + p_boost) / 2

    # Platt calibration on a time-later slice of the validation data.
    cal_split = max(20, int(len(raw) * 0.5))
    calibrator = LogisticRegression(max_iter=1000)
    calibrator.fit(raw[:cal_split].reshape(-1, 1), y_test.iloc[:cal_split])
    p_cal = calibrator.predict_proba(raw[cal_split:].reshape(-1, 1))[:, 1]
    y_cal = y_test.iloc[cal_split:]

    fold_scores = []
    for train_end, test_end in walk_forward_indices(len(x), 9):
        model = HistGradientBoostingClassifier(max_iter=180, learning_rate=0.05, max_leaf_nodes=12, random_state=7)
        model.fit(x.iloc[:train_end], y.iloc[:train_end])
        pred = model.predict(x.iloc[train_end:test_end])
        fold_scores.append(float(accuracy_score(y.iloc[train_end:test_end], pred)))

    blocks = {
        "3_fold_mean": float(np.mean(fold_scores[:3])) if len(fold_scores) >= 3 else None,
        "6_fold_mean": float(np.mean(fold_scores[:6])) if len(fold_scores) >= 6 else None,
        "9_fold_mean": float(np.mean(fold_scores[:9])) if len(fold_scores) >= 9 else None,
        "fold_accuracy": fold_scores,
    }
    evidence_pass = bool(
        len(fold_scores) >= 9
        and blocks["3_fold_mean"] >= 0.52
        and blocks["6_fold_mean"] >= 0.52
        and blocks["9_fold_mean"] >= 0.52
    )

    pack = {
        "version": "ensemble-v1",
        "mode": mode,
        "logistic": logistic,
        "boosting": boosting,
        "calibrator": calibrator,
        "evidence": "3/6/9 walk-forward passed" if evidence_pass else "3/6/9 walk-forward not passed",
        "walk_forward": blocks,
        "rows": int(len(x)),
        "test_accuracy": float(accuracy_score(y_cal, (p_cal >= 0.5).astype(int))),
        "brier": float(brier_score_loss(y_cal, p_cal)),
        "log_loss": float(log_loss(y_cal, np.clip(p_cal, 1e-5, 1 - 1e-5))),
        "ready": evidence_pass,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pack, out_dir / f"{mode.lower()}_probability.joblib")
    return {k: v for k, v in pack.items() if k not in {"logistic", "boosting", "calibrator"}}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Train TradeBot SCALP/SWING probability models")
    parser.add_argument("--bars", type=int, default=5000)
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT")
    parser.add_argument("--out", default="models")
    args = parser.parse_args()

    out = Path(args.out)
    summary = {}
    for mode, cfg in MODE_CONFIG.items():
        datasets = []
        for symbol in [s.strip().upper() for s in args.symbols.split(",") if s.strip()]:
            df = await fetch_history(symbol, cfg["interval"], args.bars)
            x, y = make_dataset(df, mode)
            datasets.append((x, y))
        x = pd.concat([a for a, _ in datasets], ignore_index=True)
        y = pd.concat([b for _, b in datasets], ignore_index=True)
        summary[mode] = train_mode(x, y, mode, out)
        print(mode, json.dumps(summary[mode], indent=2))
    (out / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
