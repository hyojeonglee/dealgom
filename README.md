# Dealgom

A lightweight, event-driven agent pipeline that collects baby-product hot deals (diapers, formula, wipes, etc.), normalizes pricing, and notifies you when a deal is actually worth buying.

Built to run locally with minimal infrastructure—no Docker or cloud required.

## Architecture

Each agent runs as an independent process and communicates asynchronously via **Redis Streams**:

- **Collector** *(implemented, sample mode)*: Fetches deal listings, deduplicates via SQLite, and publishes `RawDeal` messages to `deal.raw`.
- **Normalizer** *(planned)*: Parses product titles to extract brand, stage/size, total count, and unit price (`deal.normalized`).
- **Analyst** *(planned)*: Evaluates deals against historical price data.
- **Advisor** *(planned)*: Filters by baby's age/weight and sends Telegram notifications.

## Tech Stack

- Python 3.12 (`uv`)
- Redis Streams (`redis`)
- SQLite (`store.py`)
- Pydantic (`schemas.py`)
- Honcho (`Procfile`)

## Quick Start

1. **Install dependencies**

   ```bash
   uv sync
   ```

2. **Start Redis**

   ```bash
   brew services start redis
   redis-cli ping  # PONG
   ```

3. **Configure environment**

   Create a `.env` file in the project root:

   ```env
   REDIS_URL=redis://localhost:6379
   TELEGRAM_BOT_TOKEN=
   TELEGRAM_CHAT_ID=
   ANTHROPIC_API_KEY=
   ```

4. **Run offline tests** (no outbound HTTP requests)

   ```bash
   uv run pytest
   ```

5. **Run agents locally**

   ```bash
   uv run honcho start
   ```
