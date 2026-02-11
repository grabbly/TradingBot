# EMA Crossover Trading Bot

Automated swing trading bot based on Dual EMA Crossover strategy with entry confirmation.

## 📊 Strategy

- **Indicators**: EMA 5 and EMA 20
- **Entry**: Bullish crossover + X% growth confirmation
- **Exit**: Bearish crossover
- **Risk**: 2.5% stop-loss, one position per instrument

## 🏗️ Project Structure

```
TradingBot/
├── config/
│   └── settings.json       # Strategy parameters
├── src/
│   ├── ema.js              # EMA calculation
│   └── signals.js          # Signal logic
├── db/
│   ├── schema.sql          # PostgreSQL schema
│   ├── migrations/         # DB migrations
│   ├── apply_migrations.sh # Migration script
│   └── MIGRATIONS.md       # Migration guide
├── strategy_v1/
│   ├── workflows/          # n8n workflow files
│   └── CREDENTIALS_SETUP.md
└── scripts/
    ├── backtest_*.py       # Backtesting tools
    └── load_historical_data.py
```

## 🚀 Quick Start

### 1. Setup Alpaca

1. Register at [alpaca.markets](https://alpaca.markets)
2. Get API keys (Paper Trading)
3. Follow instructions in `strategy_v1/CREDENTIALS_SETUP.md`

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

### 3. Import workflow to n8n

1. Open n8n
2. Settings → Import from File
3. Select workflow file from `strategy_v1/workflows/`
4. Configure credentials and parameters

### 4. Run

Activate workflow - bot starts analyzing market automatically

## ⚙️ Configuration

Edit `config/settings.json`:

```json
{
  "strategy": {
    "symbol": "NVDA",
    "timeframe": "1Hour",
    "confirmationPercent": 0.75
  },
  "riskManagement": {
    "stopLossPercent": 2.5,
    "positionSize": 10
  }
}
```

## 📱 Notifications and Logging

- **Telegram**: Alerts about signals and trades
- **PostgreSQL**: Event log + statistics

## 🗄️ Database Migrations

```bash
# Apply all migrations
./db/apply_migrations.sh
```

See `db/MIGRATIONS.md` for details

## ⚠️ Important

- **Start with Paper Trading** — test without risk
- **Backtest** — test on historical data (`scripts/backtest_*.py`)
- **Monitor** — regularly check bot performance
- Don't use in live trading until verified

## 📈 Alpaca API Endpoints

| Action | Method | URL |
|--------|--------|-----|
| Account | GET | `/v2/account` |
| Positions | GET | `/v2/positions` |
| Create Order | POST | `/v2/orders` |
| Close Position | DELETE | `/v2/positions/{symbol}` |
| OHLC Data | GET | `/v2/stocks/{symbol}/bars` |

## 🔒 Security

- **Never commit `.env`** - contains sensitive credentials
- Store all API keys in environment variables
- See `SECURITY_CHECKLIST.md` for guidelines
- See `GIT_CLEANUP_GUIDE.md` to remove secrets from history

## 📚 Documentation

- `ARCHITECTURE.md` - System architecture
- `V2_SYSTEM_OVERVIEW.md` - Phase 2 features
- `GIT_CLEANUP_GUIDE.md` - Git security guide
- `CLEANUP_SUMMARY.md` - Security cleanup summary

## 📄 License

MIT
