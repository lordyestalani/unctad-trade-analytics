"""Validate the trade CSV and upsert the reporting subset into PostgreSQL."""

import os
from decimal import Decimal
from pathlib import Path

import psycopg

from validate_csv import DEFAULT_PATH, MEASURES, read_and_validate


def main() -> None:
    trade = read_and_validate(DEFAULT_PATH)
    print(f"Validation passed: {len(trade)} records.")

    columns = ["Economy", "Economy Label", "Year", "Flow", "Flow Label"] + MEASURES
    rows = [
        (*row[:5], *(Decimal(str(value)) for value in row[5:]))
        for row in trade[columns].itertuples(index=False, name=None)
    ]
    schema = Path(__file__).resolve().parents[1] / "sql/001_create_tables.sql"
    reporting_view = schema.with_name("002_create_reporting_view.sql")

    with psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema.read_text(encoding="utf-8"))
            cursor.executemany(
                """
                INSERT INTO trade (
                    economy_code, economy_name, year, flow_code, flow_name,
                    trade_value_million_usd, world_share_pct, growth_yoy_pct
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (economy_code, year, flow_code) DO UPDATE SET
                    economy_name = EXCLUDED.economy_name,
                    flow_name = EXCLUDED.flow_name,
                    trade_value_million_usd = EXCLUDED.trade_value_million_usd,
                    world_share_pct = EXCLUDED.world_share_pct,
                    growth_yoy_pct = EXCLUDED.growth_yoy_pct
                """,
                rows,
            )
            cursor.execute(reporting_view.read_text(encoding="utf-8"))

    print(f"Loaded {len(rows)} records into trade (inserted or updated).")
    print("Reporting view ready: trade_summary.")


if __name__ == "__main__":
    main()
