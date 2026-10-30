# Philippine Trade Trends

A small data engineering and Power BI project using UNCTAD merchandise trade data.

**Question:** How did Philippine exports and trade balance perform against Indonesia, Malaysia, Thailand, and Viet Nam from 2015 to 2024?

## Project scope

- Five countries, ten years, exports and imports: 100 observations in the planned reporting subset.
- Measures: trade value, annual growth, share of world trade, and calculated trade balance (exports minus imports).
- Values are in millions of US dollars at current prices. Growth reflects nominal values, not changes in trade volumes alone.

## Architecture

```text
Raw UNCTAD CSV -> Python ETL -> PostgreSQL -> Power BI Desktop
                 (planned)    (Docker)      (Windows)
```

Docker Compose currently runs PostgreSQL 17. The Python ETL container, database tables, and Power BI report will be added in later steps. PostgreSQL stores its data in a named Docker volume. Power BI Desktop runs on the host computer.

## Data

Source: [UNCTAD Data Centre](https://unctadstat.unctad.org/datacentre/), **Merchandise: Trade - Annual** (`US.TradeMerchTotal`).

The original download is preserved at `data/raw/US_TradeMerchTotal.csv`. It contains 46,108 records covering 1948–2025 and 309 geographic entries, including countries and overlapping economy groups. The pipeline will select individual countries rather than sum those groups.

The selected 2015–2024 subset has 100 records, no missing values in the three measures, and no duplicate country–year–flow keys. Economy codes must be preserved as text. Source missing-value markers and footnotes will be retained during processing.

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

## Connection settings

For Power BI Desktop, use **Get data > PostgreSQL database** with:

| Setting | Value |
| --- | --- |
| Server | `localhost:5432` |
| Database | `unctad` |
| Username | `unctad` |
| Password | Your local `POSTGRES_PASSWORD` in `.env` |

The database port binds only to `127.0.0.1`. If port 5432 is already in use, change `POSTGRES_PORT` in `.env` and use the new port in Power BI. The future ETL container will connect to host `postgres` on port `5432` inside the Compose network.

The database is initially empty; the reporting tables will be created during the ETL milestone.

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

1. Add the Python ETL container and validate the reporting subset.
2. Create PostgreSQL tables and a repeatable load without duplicate records.
3. Add SQL reporting views and verify totals.
4. Build a Power BI report with export trends, country comparisons, and trade balances.
5. Document findings and add dashboard screenshots.

This README will be updated as each milestone is implemented.
