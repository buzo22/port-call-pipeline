import duckdb

con = duckdb.connect("data/warehouse.duckdb", read_only=True)

# Find the overlapping pair automatically.
pair = con.sql("""
    SELECT a.mmsi,
           least(a.entered_at, b.entered_at)   AS t_from,
           greatest(a.exited_at, b.exited_at)  AS t_to,
           a.port_code AS a_port, a.position_count AS a_pings,
           b.port_code AS b_port, b.position_count AS b_pings
    FROM int_port_visits a
    JOIN int_port_visits b
      ON a.mmsi = b.mmsi AND a.visit_id < b.visit_id
     AND a.entered_at < b.exited_at AND b.entered_at < a.exited_at
""").fetchone()
print("Overlap:", pair)
mmsi, t_from, t_to = pair[0], pair[1], pair[2]

# Every ping for that vessel in the overlap window, with the port it matched (if any).
print(con.sql(f"""
    SELECT d.observed_at,
           round(d.lat, 3) AS lat, round(d.lon, 3) AS lon, d.sog_knots,
           p.port_code,
           round(d.knots_from_prev) AS kn_from_prev,
           round(d.knots_to_next)   AS kn_to_next,
           d.is_position_spike
    FROM int_positions_despiked d
    LEFT JOIN int_port_positions p
      ON p.mmsi = d.mmsi AND p.observed_at = d.observed_at
    WHERE d.mmsi = {mmsi}
      AND d.observed_at BETWEEN TIMESTAMP '{t_from}' - INTERVAL 1 HOUR
                            AND TIMESTAMP '{t_to}'   + INTERVAL 1 HOUR
      AND (p.port_code IS NULL OR p.port_code IN ('{pair[3]}', '{pair[5]}'))
    ORDER BY d.observed_at
""").limit(80))
