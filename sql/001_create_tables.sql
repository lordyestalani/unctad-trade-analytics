CREATE TABLE IF NOT EXISTS trade (
    economy_code TEXT NOT NULL,
    economy_name TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year BETWEEN 2015 AND 2024),
    flow_code TEXT NOT NULL CHECK (flow_code IN ('01', '02')),
    flow_name TEXT NOT NULL,
    trade_value_million_usd NUMERIC NOT NULL,
    world_share_pct NUMERIC NOT NULL,
    growth_yoy_pct NUMERIC NOT NULL,
    PRIMARY KEY (economy_code, year, flow_code)
);
