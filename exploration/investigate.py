import duckdb

con = duckdb.connect("data/warehouse.duckdb", read_only=True)

print("\n--- Overlapping visits ---")
print(con.sql("""
    WITH o AS (
        SELECT a.mmsi,
               a.port_code AS a_port, a.entered_at AS a_in, a.exited_at AS a_out, a.position_count AS a_pings,
               b.port_code AS b_port, b.entered_at AS b_in, b.exited_at AS b_out, b.position_count AS b_pings
        FROM int_port_visits a
        JOIN int_port_visits b
          ON a.mmsi = b.mmsi
         AND a.visit_id < b.visit_id
         AND a.entered_at < b.exited_at
         AND b.entered_at < a.exited_at
    )
    SELECT o.*,
           (SELECT string_agg(DISTINCT vessel_name, ' / ')
            FROM stg_ais_positions s WHERE s.mmsi = o.mmsi) AS names_reported
    FROM o ORDER BY mmsi, a_in
"""))

print("\n--- Pings per hour on 2024-01-14 (outage check) ---")
print(con.sql("""
    PIVOT (
        SELECT hour(observed_at) AS hour_utc, port_code
        FROM int_port_positions
        WHERE observed_at::date = DATE '2024-01-14'
    )
    ON port_code USING count(*)
    ORDER BY hour_utc
"""))
