# TradeBot — AI Long/Short Trading Engine

A modular crypto trading research platform with LONG/SHORT strategies, separate SCALP/SWING probability models, risk controls, paper execution and push notifications.

> ⚠️ **Paper trading only in this release.** No live orders are sent.

## Strategy architecture

### SCALP
- 5m market analysis
- Higher signal frequency
- Tighter ATR protection
- Up to 5 scalp positions
- Default confidence threshold: 87

### SWING
- 1h market analysis
- More selective setups
- Wider ATR protection
- Up to 3 swing positions
- Default confidence threshold: 82

The timeframe controls analysis, not the holding period. There is no automatic time-based exit.

## Probability Engine

The system no longer treats the legacy 0–100 score as a literal probability. The new engine maintains two independent models: one for SCALP and one for SWING.

Each model uses:
- technical/volatility/momentum/volume features
- Fibonacci 38.2 / 50 / 61.8 / 78.6 proximity as features, not hard-coded signals
- LONG/SHORT as a model feature
- logistic regression + histogram gradient boosting ensemble
- probability calibration
- positive Expected Value filtering
- chronological 3/6/9 walk-forward validation

A model is only accepted by the live engine when the 3/6/9 validation passes. Otherwise the bot stays on a transparent rule-based fallback.

Expected value is calculated as:

`EV(R) = P(win) × reward_R - (1 - P(win)) × 1R`

A validated setup must have positive edge before the model can promote it.

## Training

Install dependencies first, then run:

```bash
python scripts/train_probability_models.py --bars 5000
```

The trainer downloads paginated Binance public candles, creates TP-before-SL labels for supervised learning, trains SCALP and SWING independently, calibrates the ensemble, evaluates chronological walk-forward blocks and saves local `.joblib` artifacts under `models/`.

The look-ahead used during training exists only to create a supervised label. It is **not** a maximum live holding time.

## Current MVP

- Binance public market-data API
- Multi-symbol LONG/SHORT scanning
- Separate SCALP/SWING modes
- Probability + confidence + Expected Value in the API/UI
- Risk-based position sizing
- Separate scalp/swing position caps
- Daily loss guard
- Side-aware paper execution
- No time-based trade expiry
- Browser/OS push notification infrastructure
- Dark-tech responsive dashboard

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/index.html`.

## Useful endpoints

```text
GET  /scan?mode=SCALP
GET  /scan?mode=SWING
GET  /scan/all
GET  /ai/status
GET  /positions
POST /trade/SCALP/LONG/BTCUSDT
POST /trade/SCALP/SHORT/BTCUSDT
POST /trade/SWING/LONG/BTCUSDT
POST /trade/SWING/SHORT/BTCUSDT
GET  /notifications/config
```

## Safety model

A confidence of 87 is only a display/decision threshold. It is not a guaranteed 87% win rate. Live execution remains disabled until the probability models have enough data, pass walk-forward validation and the whole strategy has been backtested in paper trading.
