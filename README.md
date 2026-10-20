# AI Trading Copilot - Production Terminal

An advanced, production-grade **AI Trading Copilot** designed to assist traders through AI-driven quantitative analytics, real-time pattern tracking, and automated forecasting, while maintaining a strict zero-trade-execution policy (the human makes all execution choices).

---

## Technical Stack

* **Frontend**: React, TypeScript, Vite, Tailwind CSS, Zustand state management, React Query, and TradingView's Lightweight Charts.
* **Backend**: FastAPI, Python 3.12, SQLAlchemy ORM, Alembic migrations, WebSockets, and AsyncIO tasks.
* **AI Engines**: Qwen 2.5 Instruct 8B model wrapper (via Hugging Face `transformers` & `torch`).
* **Forecasting**: Amazon Chronos-T5 time-series predictor.
* **Database**: Supabase PostgreSQL + Auth integration.
* **Orchestration**: Docker & Docker Compose.

---

## Folder Structure

```
AI TRADING COPILOT/
├── frontend/                     # React client interface
├── backend/                      # FastAPI middleware & WS manager
├── ai/                           # Qwen 3 8B model inference service
├── forecast/                     # Chronos forecasting pipeline
├── technical_analysis/           # Mathematical indicators library
├── pattern_detection/            # Trendline & candle pattern scans
├── database/                     # PostgreSQL SQL migrations
├── docker/                       # Containerization files
└── README.md                     # Central documentation
```

---

## Database Schema (Supabase PostgreSQL)

The schema defines **20 tables** featuring UUID primary keys, foreign key constraints, indexes, Row-Level Security (RLS) policies, and database-level comments:
1. `profiles`: Links user profiles to Supabase Auth.
2. `user_settings`: User leverage settings and model preferences.
3. `watchlists`: Custom symbols collections.
4. `watchlist_symbols`: Symbols tied to specific watchlists.
5. `portfolios`: Portfolio balances (cash/equity reserves).
6. `portfolio_assets`: Held quantities and cost basis.
7. `journal_entries`: Logging notes, outcome PnL, and emotions.
8. `journal_screenshots`: Attached charts screenshots.
9. `ai_analyses`: AI insights (signal type, targets, resistances).
10. `news_articles`: News streams with sentiment NLP values.
11. `alerts`: Cross-alert triggers (price crossings).
12. `alert_history`: Triggers alert occurrences.
13. `strategies`: Quantitative rules definitions (SMA periods).
14. `backtest_runs`: Execution logs of strategy backtests.
15. `backtest_trades`: Trade lists from backtest executions.
16. `notification_preferences`: Alert rules settings (email, UI).
17. `indicator_presets`: Settings presets for indicators.
18. `chart_layouts`: Saved widget grid structures.
19. `api_logs`: Audit logs tracking latency and endpoints.
20. `audit_logs`: Auditing for administrative state.

---

## FastAPI Routing Architecture

### REST API Endpoints (`/api/v1/`)
- `/profile`: Manages and fetches user profiles & settings.
- `/watchlist`: CRUD operations for user-tracked lists.
- `/portfolio`: Tracks assets and simulates buy/sell execution logic.
- `/journal`: Logs entries and requests AI evaluations.
- `/alerts`: Deploy and delete custom price triggers.
- `/strategy` & `/backtest/run`: Forms backtest simulations, logging return ratios and curve JSONs.
- `/news`: Pulls news categorised by bullish/bearish NLP sentiment.
- `/analysis/{symbol}/{timeframe}`: Retrieves cached quantitative AI assessments.

### WebSockets Stream (`/ws`)
Client WebSockets connect to the persistent gateway server, which consumes live, auto-reconnecting ticker feeds directly from Binance (`wss://stream.binance.com:9443/ws`), broadcasting aggregated price ticks, order book bids/asks, and trade signals.

---

## Deployment & Setup

### Docker Compose Quickstart
Start all services (Frontend Nginx, FastAPI Backend, Qwen AI, and Chronos Forecast):
```bash
docker-compose -f docker/docker-compose.yml up --build
```
- **React UI**: `http://localhost`
- **FastAPI Gateway**: `http://localhost:8000`
- **AI Service**: `http://localhost:8001`
- **Forecast Service**: `http://localhost:8002`

### Environment Configurations
Copy `.env.example` to `.env` and fill in your Supabase DB URL and JWT Secret:
```bash
cp .env.example .env
```
