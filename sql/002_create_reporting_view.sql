CREATE OR REPLACE VIEW trade_summary AS
WITH totals AS (
    SELECT
        economy_code,
        economy_name,
        year,
        SUM(trade_value_million_usd) FILTER (WHERE flow_code = '02') AS exports_million_usd,
        SUM(trade_value_million_usd) FILTER (WHERE flow_code = '01') AS imports_million_usd
    FROM trade
    GROUP BY economy_code, economy_name, year
)
SELECT
    economy_code,
    economy_name,
    year,
    exports_million_usd,
    imports_million_usd,
    exports_million_usd - imports_million_usd AS trade_balance_million_usd
FROM totals;
