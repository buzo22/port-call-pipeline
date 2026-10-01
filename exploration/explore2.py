import duckdb

con = duckdb.connect()
con.execute("INSTALL spatial; LOAD spatial;")
con.execute("""
    CREATE VIEW ais AS
    SELECT *, ST_X(geometry) AS lon, ST_Y(geometry) AS lat
    FROM read_parquet('data/ais-2024-01-15.parquet')
""")
con.execute("""
    CREATE VIEW la AS
    SELECT * FROM ais
    WHERE lat BETWEEN 33.67 AND 33.82 AND lon BETWEEN -118.33 AND -118.15
      AND vessel_type BETWEEN 70 AND 79
""")

def show(title, sql):
    print(f"\n--- {title} ---")
    print(con.sql(sql))

show("A. Are duplicates identical, or do they conflict?", """
    WITH d AS (
        SELECT mmsi, base_date_time,
               count(DISTINCT (lat, lon, sog)) AS distinct_versions
        FROM ais GROUP BY ALL HAVING count(*) > 1
    )
    SELECT distinct_versions, count(*) AS groups FROM d GROUP BY 1 ORDER BY 1
""")

show("B. Which vessels report over 50 knots?", """
    SELECT vessel_type, count(*) AS rows, count(DISTINCT mmsi) AS vessels,
           round(max(sog), 1) AS max_sog
    FROM ais WHERE sog > 50
    GROUP BY 1 ORDER BY rows DESC LIMIT 8
""")

show("C. Navigational status of cargo ships near LA", """
    SELECT status, count(*) AS pings, count(DISTINCT mmsi) AS ships
    FROM la GROUP BY 1 ORDER BY pings DESC
""")

show("D. Cargo ships near LA that actually moved", """
    SELECT mmsi, any_value(vessel_name) AS name, count(*) AS pings,
           min(base_date_time) AS first_seen, max(base_date_time) AS last_seen,
           round(max(sog), 1) AS max_sog
    FROM la GROUP BY mmsi
    HAVING max(sog) > 5 AND min(sog) < 0.5
    ORDER BY pings DESC LIMIT 5
""")
