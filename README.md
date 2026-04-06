# BotNitoTrading

Automated forex trading bot that uses a NEAT-evolved neural network to make buy/sell/hold decisions on live OANDA accounts. The network is trained offline using neuroevolution and deployed in a real-time polling loop that executes market orders via the OANDA v3 REST API.

## Architecture

```
┌──────────────────────────────────────────────┐
│                   bot.py                      │
│             TradingBot main loop              │
│  - polls candles every 10s (M10 granularity)  │
│  - fetches macro indicators once per day      │
└──────────┬───────────────────┬───────────────┘
           │                   │
  ┌────────▼────────┐  ┌───────▼────────────┐
  │  technicals.py  │  │  trade_manager.py  │
  │  NEAT NN engine │  │  position & order  │
  │  + indicators   │  │  management        │
  └────────┬────────┘  └───────┬────────────┘
           │                   │
           └─────────┬─────────┘
                     │
           ┌─────────▼─────────┐
           │    oanda_api.py    │
           │  REST client v3    │
           │  candles, orders,  │
           │  trades, pricing   │
           └─────────┬──────────┘
                     │
       ┌─────────────▼──────────────────┐
       │         External APIs           │
       │  OANDA v3         (execution)   │
       │  Alpha Vantage    (Fed rate)    │
       │  Banxico SIE API  (MX rate)     │
       │  CNN Fear & Greed (sentiment)   │
       │  Yahoo Finance    (VIX)         │
       └─────────────────────────────────┘
```

## Decision Engine

The neural network receives 9 inputs on each candle close and outputs a continuous signal:

| Input | Source |
|-------|--------|
| Volume | OANDA candle |
| Open | OANDA candle |
| High | OANDA candle |
| Low | OANDA candle |
| Close | OANDA candle |
| Banxico interest rate | Banxico SIE API |
| Fed funds rate | Alpha Vantage |
| Fear & Greed Index | CNN |
| VIX | Yahoo Finance |

- Output > 0.5 → **BUY**
- Output < -0.5 → **SELL**
- Otherwise → **HOLD**

Network topology and weights are evolved offline using [NEAT-Python](https://neat-python.readthedocs.io/). Trained genomes are saved as `.pkl` files and loaded at runtime.

## Key Components

| File | Responsibility |
|------|---------------|
| `bot.py` | Main `TradingBot` class — loop, timing, indicator cache |
| `technicals.py` | NEAT inference + indicator fetching (Fed, Banxico, VIX, FnG) |
| `trade_manager.py` | Position tracking, open/close order logic |
| `oanda_api.py` | OANDA REST client — candles, market orders, SL/TP, open trades |
| `oanda_trade.py` | Trade data model |
| `oanda_price.py` | Price data model |
| `settings.py` | Loads pair config from `settings.json` |
| `defs.py` | Constants, credentials (via env vars), signal enums |
| `emailer.py` | SMTP alerts on trade events and errors |
| `log_wrapper.py` | Per-component rotating log files |
| `timing.py` | Candle-ready detection per pair |

## Setup

```bash
# 1. Clone and install dependencies
pip install -r requirements.txt

# 2. Copy env template and fill in your credentials
cp .env.example .env

# 3. Add your trained NEAT genome to the brains/ directory
#    (see brains/config-experiment-38d.txt for network config)

# 4. Configure trading pairs in settings.json
#    Example: {"USD_MXN": {"pair": "USD_MXN", "units": 1000, "short_ma": 2, "long_ma": 8}}

# 5. Run
python bot.py
```

## Configuration

`settings.json` controls which pairs to trade and the MA parameters used for signal preprocessing:

```json
{
  "USD_MXN": {
    "pair": "USD_MXN",
    "units": 1000,
    "short_ma": 2,
    "long_ma": 8
  }
}
```

Set `OANDA_URL` in `.env` to the practice endpoint (`https://api-fxpractice.oanda.com/v3`) to run against a paper trading account before going live.

## Training

NEAT genomes are trained separately using the experiment configs in `brains/`. The training loop evaluates genomes on historical candle data + macro indicators, scores them by P&L and Sharpe ratio, and evolves the population over generations. Winning genomes are serialized to `.pkl` and loaded by `technicals.py` at runtime.

## Disclaimer

This is a research and educational project. Forex trading involves substantial risk of loss. Past backtest performance does not guarantee live results.
