# TradeBot — AI Long/Short Trading Engine

A modular crypto trading research platform with LONG/SHORT technical screening, separate SCALP/SWING profiles, risk controls and paper execution.

> ⚠️ **Paper trading only in this release.** No live orders are sent.

## Strategy profiles

### SCALP
- 5m analysis timeframe
- Higher signal frequency
- Tighter ATR-based protection
- Up to 5 scalp positions
- Default minimum confidence: 87
- Designed for shorter intraday opportunities

### SWING
- 1h analysis timeframe
- More selective setups
- Wider ATR-based protection
- Up to 3 swing positions
- Default minimum confidence: 82
- Designed to capture larger multi-hour moves

The timeframe controls how the market is analyzed; it does **not** impose a holding-period limit.

## Trade lifecycle

Trades are **not time-based**. There is no fixed holding period and no automatic "close after X minutes/hours/days" rule.

A position remains open until a market/strategy exit occurs:

- Stop-loss is hit
- Take-profit is hit
- Future strategy logic explicitly signals an exit or reversal
- A global risk/emergency rule explicitly closes or blocks exposure

This allows a scalp to stay open longer when the setup remains valid and a swing position to close quickly when its stop or target is reached.

## Current MVP

- Binance public market-data API for candles
- Multi-symbol LONG and SHORT scanner
- Separate SCALP and SWING profiles
- RSI, EMA trend, MACD histogram, ATR and breakout/breakdown logic
- 0–100 setup confidence score
- Risk-based position sizing
- Separate position caps for scalp and swing
- Daily loss guard
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

## Example endpoints

```text
GET  /scan?mode=SCALP
GET  /scan?mode=SWING
GET  /scan/all
POST /trade/SCALP/LONG/BTCUSDT
POST /trade/SCALP/SHORT/BTCUSDT
POST /trade/SWING/LONG/BTCUSDT
POST /trade/SWING/SHORT/BTCUSDT
GET  /positions
```

## Configuration

Copy `.env.example` to `.env` and adjust values. No exchange API key is required for the public-data scanner.

## Safety model

The bot does not treat confidence as a literal probability of profit. A confidence of `87` means the configured rule engine scores the setup at 87/100. Live execution must remain disabled until the strategy has been backtested and validated.
