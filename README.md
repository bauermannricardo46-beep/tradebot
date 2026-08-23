# TradeBot — AI Short Trading Engine

A modular crypto short-trading research platform with technical screening, risk controls and paper execution.

> ⚠️ **Paper trading only in this first release.** No live orders are sent.

## Architecture

- `scanner/` — market data + technical setup detection
- `risk/` — position sizing and safety limits
- `execution/` — paper order execution
- `api/` — FastAPI service
- `tests/` — automated tests

## Current MVP

- Binance public market-data API for candles
- Multi-symbol short scanner
- RSI, EMA trend, MACD histogram, ATR and breakdown/rejection logic
- 0–100 setup confidence score
- Risk-based position sizing
- Max concurrent positions and daily loss guard
- Paper trade lifecycle with stop-loss / take-profit handling
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
