# TradeBot — AI Long/Short Trading Engine

TradeBot is a crypto trading research platform with LONG/SHORT strategies, separate SCALP/SWING probability models, multi-timeframe market structure, dynamic exits, persistent live data collection, paper execution and push notifications.

> ⚠️ **Paper trading only.** This release sends no live exchange orders.

## Multi-timeframe strategy

### SCALP
- Primary analysis: 5m
- Context: 1m / 5m / 15m / 1h / 4h
- Designed for frequent short-term opportunities
- A scalp has **no maximum holding time**
- Dynamic TP1 / TP2 plus trailing exit

### SWING
- Primary analysis: 1h
- Context: 5m / 15m / 1h / 4h
- Designed to capture larger multi-hour moves
- A swing has **no maximum holding time**
- Dynamic structure-based targets plus trailing exit

The timeframe is only the lens used to analyze the market. It does not force a position to close after that amount of time.

## Capture-the-move logic

The strategy combines:
- multi-timeframe trend alignment
- swing-high / swing-low structure
- Fibonacci 38.2 / 50 / 61.8 / 78.6 proximity
- volatility-aware stop placement
- probabilistic setup scoring
- Expected Value filtering
- extended TP2 targets
- dynamic trailing stops after TP1

The goal is not to predict the exact absolute low or high. The goal is to enter where the probability/expected value is favorable and let a valid movement continue instead of cutting it off because a clock expired.

## Probability Engine

SCALP and SWING use independent probability models. Each model can combine technical, momentum, volatility, volume and Fibonacci-derived features with logistic regression + histogram gradient boosting and probability calibration. A model is accepted at runtime only when it has passed the configured chronological 3/6/9 walk-forward validation.

Expected value:

`EV(R) = P(win) × reward_R - (1 - P(win)) × 1R`

## Live data collection

When the server starts, the collector automatically gathers live Binance public candle data and qualifying analyses at the configured interval. Data is stored locally in SQLite:

```text
data/
└── tradebot.db
```

The database persists between restarts and stores market snapshots, analysis snapshots and outcome labels. The Windows launcher redirects this to `%LOCALAPPDATA%\TradeBotAI\data`.

Useful endpoints:

```text
GET  /data/stats
GET  /data/analyses?limit=50
POST /data/collect-now
GET  /ai/status
```

## Training

```bash
python scripts/train_probability_models.py --bars 5000
```

The trainer saves validated local model artifacts under `models/`. The Windows launcher uses `%LOCALAPPDATA%\TradeBotAI\models`.

## Windows app

The repository contains a PyInstaller configuration and GitHub Actions workflow that builds a Windows x64 artifact named `TradeBot-Windows-x64`.

Start:

```text
TradeBot.exe
```

The launcher shows a startup animation, starts the local FastAPI engine, waits for the health endpoint and opens the embedded desktop Control Center.

## Safety

Confidence is not a guarantee of profit. Live exchange execution remains disabled. New models are only accepted when their validation gate passes, and the trading engine continues to use risk limits and paper execution during development.
