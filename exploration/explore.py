import duckdb

con = duckdb.connect()
con.execute("INSTALL spatial; LOAD spatial;")
con.execute("""
    CREATE VIEW ais AS
    SELECT *, ST_X(geometry) AS lon, ST_Y(geometry) AS lat
    FROM read_parquet('data/ais-2024-01-15.parquet')
""")

def show(title, sql):
    print(f"\n--- {title} ---")
    print(con.sql(sql))

show("1. Duplicate pings (same vessel, same timestamp)", """
    SELECT count(*) AS duplicated_groups, sum(n - 1) AS extra_rows FROM (
        SELECT mmsi, base_date_time, count(*) AS n FROM ais
        GROUP BY ALL HAVING count(*) > 1
    )
""")

show("2. Speed: nulls and suspicious values", """
    SELECT count(*) FILTER (WHERE sog IS NULL)  AS sog_null,
           count(*) FILTER (WHERE sog > 50)     AS sog_over_50,
           max(sog)                             AS sog_max
    FROM ais
""")

show("3. Blank strings vs NULL in imo", """
    SELECT count(*) FILTER (WHERE imo IS NULL) AS imo_null,
           count(*) FILTER (WHERE imo = '')    AS imo_blank
    FROM ais
""")

show("4. Invalid coordinates", """
    SELECT count(*) AS n FROM ais
    WHERE lat NOT BETWEEN -90 AND 90 OR lon NOT BETWEEN -180 AND 180
""")

show("5. Busiest cargo ships near Los Angeles / Long Beach", """
    SELECT mmsi, any_value(vessel_name) AS name, count(*) AS pings,
           min(base_date_time) AS first_seen, max(base_date_time) AS last_seen,
           round(min(sog), 1) AS min_sog, round(max(sog), 1) AS max_sog
    FROM ais
    WHERE lat BETWEEN 33.67 AND 33.82
      AND lon BETWEEN -118.33 AND -118.15
      AND vessel_type BETWEEN 70 AND 79
    GROUP BY mmsi ORDER BY pings DESC LIMIT 5
""")
