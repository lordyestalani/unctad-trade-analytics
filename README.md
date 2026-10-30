# Philippine Trade Trends

A small data engineering and Power BI project using UNCTAD merchandise trade data.

**Question:** How did Philippine exports and trade balance perform against Indonesia, Malaysia, Thailand, and Viet Nam from 2015 to 2024?

## Project scope

- Five countries, ten years, exports and imports: 100 observations in the reporting subset.
- Measures: trade value, annual growth, share of world trade, and calculated trade balance (exports minus imports).
- Values are in millions of US dollars at current prices. Growth reflects nominal values, not changes in trade volumes alone.

## Architecture

```text
Raw UNCTAD CSV -> Python ETL -> PostgreSQL -> Power BI Desktop
                 (Docker)     (Docker)      (planned)
```

Docker Compose runs PostgreSQL 17 and a one-off Python ETL service. Python 3.12 uses pandas to validate the CSV and Psycopg to load it. PostgreSQL stores its data in a named Docker volume. Power BI Desktop will run on the host computer.

## Data

Source: [UNCTAD Data Centre](https://unctadstat.unctad.org/datacentre/), **Merchandise: Trade - Annual** (`US.TradeMerchTotal`).

The original download is preserved at `data/raw/US_TradeMerchTotal.csv`. It contains 46,108 records covering 1948–2025 and 309 geographic entries, including countries and overlapping economy groups. The pipeline selects individual countries rather than summing those groups.

The selected 2015–2024 subset has 100 records, no missing values in the three measures, and no duplicate country–year–flow keys. Economy and flow codes are preserved as text. Source missing-value markers and footnotes remain in the raw CSV; the reporting table stores the codes, labels, year, and three numeric measures.

## Run PostgreSQL locally

Prerequisite: Docker Desktop running with Linux containers and Docker Compose available. Run these commands from the repository root.

1. Create your local settings (PowerShell):

   ```powershell
   Copy-Item .env.example .env
   ```

   Edit `.env` and replace the example password before starting. Skip the copy if `.env` already exists. `.env` is ignored by Git; `.env.example` is the shareable template.

2. Validate the configuration and start PostgreSQL:

   ```powershell
   docker compose config --quiet
   docker compose up -d --wait
   docker compose ps
   ```

   The first start downloads the PostgreSQL image. The service should report `healthy`.

3. Verify the database:

   ```powershell
   docker compose exec postgres psql -U unctad -d unctad -c "SELECT current_database(), current_user;"
   ```

   If you change the database or username in `.env`, use those values in the command.

## Build the Python image

The Dockerfile uses the official `python:3.12-slim-bookworm` image with `/app` as its working directory. Python writes logs immediately and skips bytecode files.

```powershell
docker build -t unctad-etl:local .
docker run --rm unctad-etl:local python --version
```

Dependencies are pinned in `requirements.txt`. Psycopg uses the binary extra so no compiler or separate PostgreSQL client library installation is needed.

Verify the installed packages:

```powershell
docker run --rm unctad-etl:local python -c "import pandas, psycopg; print('pandas', pandas.__version__); print('psycopg', psycopg.__version__)"
docker run --rm unctad-etl:local python -m pip check
```

The default command runs `src/load_trade.py`; use Compose to supply its database settings and mount the raw data. No local Python installation is required. `.dockerignore` keeps local credentials, Git history, and data out of the build context.

## Validate the CSV

Run the script using the Python image and a read-only mount of the repository:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/app,readonly" unctad-etl:local python src/validate_csv.py
```

The script selects the five countries for 2015–2024 and checks required columns, all 100 country–year–flow combinations, duplicate keys, matching codes and labels, and numeric measures without missing or infinite values. It retains the source columns, reads economy and flow codes as text, prints a summary, and exits with a nonzero status if validation fails. It does not write files or load PostgreSQL.

## Load PostgreSQL

```powershell
docker compose run --build --rm etl
```

Compose starts PostgreSQL if needed and waits for it to become healthy. The ETL service runs only when explicitly requested; ordinary `docker compose up` starts just PostgreSQL.

`src/load_trade.py` validates the CSV before connecting, creates the `trade` table from `sql/001_create_tables.sql` if needed, and loads all 100 records in one transaction. The raw directory is mounted read-only. The primary key is `(economy_code, year, flow_code)`; reruns update existing records instead of duplicating them. Database values use PostgreSQL `NUMERIC`.

Verify the load (using your configured database and username):

```powershell
docker compose exec postgres psql -U unctad -d unctad -c "SELECT COUNT(*) FROM trade;"
```

Expected count: `100`, including after a second run. `trade_value_million_usd` is in millions of US dollars; `world_share_pct` and `growth_yoy_pct` are percentages, so `5` means 5%.

## Reporting view

`sql/002_create_reporting_view.sql` defines `trade_summary`. The loader creates or replaces it in the same transaction as the data load. Run `docker compose run --build --rm etl` after changing the SQL or Python code.

The view has 50 rows: one per country and year. It provides `economy_code`, `economy_name`, `year`, `exports_million_usd`, `imports_million_usd`, and `trade_balance_million_usd` (exports minus imports). All monetary values remain in millions of current US dollars. A missing flow produces a null value rather than being treated as zero.

This is a saved query, not a separate stored copy of the data. It reflects the current `trade` table whenever queried. Select `public.trade_summary` when connecting Power BI.

```powershell
docker compose exec postgres psql -U unctad -d unctad -c "SELECT * FROM trade_summary WHERE economy_code = '608' ORDER BY year;"
```

## Connection settings

For Power BI Desktop, use **Get data > PostgreSQL database** with:

| Setting | Value |
| --- | --- |
| Server | `localhost:5432` |
| Database | `unctad` |
| Username | `unctad` |
| Password | Your local `POSTGRES_PASSWORD` in `.env` |

The database port binds only to `127.0.0.1`. If port 5432 is already in use, change `POSTGRES_PORT` in `.env` and use the new port in Power BI. The ETL container connects to host `postgres` on port `5432` inside the Compose network.

## Useful commands

```powershell
docker compose logs --tail 50 postgres
docker compose stop
docker compose start --wait
docker compose down
```

`stop` stops the container; `start` resumes it. `down` removes the containers and network while preserving the database volume; run `up -d --wait` to recreate them. Avoid `docker compose down -v` unless you intend to delete the database data.

Database credentials are initialized on the first start with an empty volume. Editing them in `.env` later does not change credentials already stored in PostgreSQL.

## Next steps

1. Build a Power BI report with export trends, country comparisons, and trade balances.
2. Document findings and add dashboard screenshots.

This README will be updated as each milestone is implemented.
