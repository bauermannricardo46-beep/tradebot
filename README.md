# TradeBot — AI Long/Short Trading Engine

A modular crypto trading research platform with LONG/SHORT technical screening, risk controls and paper execution.

> ⚠️ **Paper trading only in this release.** No live orders are sent.

## Trade lifecycle

Trades are **not time-based**. There is no fixed holding period and no automatic "close after X minutes/hours/days" rule.

A position remains open until a market/strategy exit occurs:

- Stop-loss is hit
- Take-profit is hit
- Future strategy logic explicitly signals an exit or reversal
- A global risk/emergency rule explicitly closes or blocks exposure

The timeframe controls how the market is analyzed; it does **not** determine how long a trade may remain open.

## Current MVP

- Binance public market-data API for candles
- Multi-symbol LONG and SHORT scanner
- RSI, EMA trend, MACD histogram, ATR and breakout/breakdown logic
- 0–100 setup confidence score
- Risk-based position sizing
- Max concurrent positions and daily loss guard
- Side-aware paper trade lifecycle
- Stop-loss / take-profit handling without time expiry
- REST endpoints for scanning and paper trading

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the API.

## Configuration

Copy `.env.example` to `.env` and adjust values. No exchange API key is required for the public-data scanner.

## Safety model

The bot does not treat confidence as a literal probability of profit. A confidence of `87` means the configured rule engine scores the setup at 87/100. Live execution must remain disabled until the strategy has been backtested and validated.
