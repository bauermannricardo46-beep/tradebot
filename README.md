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

The goal is not to predict the exact absolute low or high. The goal is to enter where probability/expected value is favorable and let a valid movement continue instead of cutting it off because a clock expired.

## Probability Engine

SCALP and SWING use independent probability models. Each model can combine technical, momentum, volatility, volume and Fibonacci-derived features with logistic regression + histogram gradient boosting and probability calibration. A model is accepted at runtime only when it has passed the configured chronological 3/6/9 walk-forward validation.

Expected value:

`EV(R) = P(win) × reward_R - (1 - P(win)) × 1R`

## Live data and learning dataset

When the server starts, the collector automatically gathers live Binance public candle data for every timeframe used by the strategy. It stores candles **before** storing analyses, so every new signal is anchored to a concrete source candle.

Each new setup receives a deterministic signal key:

`symbol + mode + side + timeframe + source candle open time`

This prevents the same signal from being logged repeatedly every collector cycle.

The database stores:
- multi-timeframe market candles
- setup probability/confidence/EV
- entry, SL, TP1, TP2 and trailing levels
- swing/Fibonacci levels
- analysis timeframes and model version
- model features used at signal time
- outcome status
- exit reason and exit price
- realized R
- maximum favorable/adverse excursion
- candles observed before resolution

Outcomes are evaluated on **future candles only**. A later candle can resolve a setup through the initial stop, dynamic trailing stop or extended TP2. When one candle touches both a stop and a target, the label is conservative and treats the stop as first because candle data does not reveal intrabar ordering.

Persistent data:

```text
data/
└── tradebot.db
```

The Windows launcher redirects this to `%LOCALAPPDATA%\TradeBotAI\data`.

Useful endpoints:

```text
GET  /data/stats
GET  /data/analyses?limit=50
GET  /data/training?limit=10000
POST /data/collect-now
GET  /ai/status
```

`/data/training` contains only **resolved, candle-anchored observations** suitable for model training. Legacy analyses created by older builds are preserved but are not treated as training examples until they have a valid source candle and outcome.

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

The launcher shows a startup animation, starts the local FastAPI engine, waits for the health endpoint and opens the embedded desktop Control Center. The API resolves the bundled `web` directory through the PyInstaller runtime path, so the desktop build does not depend on the current working directory.

## Safety

Confidence is not a guarantee of profit. Live exchange execution remains disabled. New models are only accepted when their validation gate passes, and the trading engine continues to use risk limits and paper execution during development.
