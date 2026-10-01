import duckdb

MMSI = 477159100  # CMA CGM MUMBAI

con = duckdb.connect()
con.execute("INSTALL spatial; LOAD spatial;")
con.execute(f"""
    CREATE VIEW ship AS
    SELECT base_date_time AS t, sog, status,
           round(ST_Y(geometry), 4) AS lat, round(ST_X(geometry), 4) AS lon,
           CASE WHEN sog < 0.5 THEN 'at rest' ELSE 'moving' END AS state
    FROM read_parquet('data/ais-2024-01-15.parquet')
    WHERE mmsi = {MMSI}
""")

print("\n--- State changes ---")
print(con.sql("""
    WITH s AS (
        SELECT *, lag(state) OVER (ORDER BY t)  AS prev_state,
                  lag(status) OVER (ORDER BY t) AS prev_status
        FROM ship
    )
    SELECT t, state, status, sog, lat, lon FROM s
    WHERE prev_state IS NULL
       OR state <> prev_state
       OR status IS DISTINCT FROM prev_status
    ORDER BY t
"""))

print("\n--- Time between pings (seconds) ---")
print(con.sql("""
    WITH g AS (SELECT epoch(t - lag(t) OVER (ORDER BY t)) AS gap FROM ship)
    SELECT round(median(gap)) AS median_gap,
           round(quantile_cont(gap, 0.95)) AS p95_gap,
           max(gap) AS max_gap
    FROM g
"""))
