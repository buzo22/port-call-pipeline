"""Land NOAA AIS days into the raw layer, filtered to port areas.

Each day is written to data/raw/ais/date=YYYY-MM-DD/positions.parquet.
Writes go to a temporary folder first and are renamed into place only on
success, so a failed run never leaves a partial day. Rerunning a day
replaces it, so loads are idempotent.
"""
import argparse
import csv
import datetime as dt
import logging
import math
import shutil
from pathlib import Path

import duckdb

from portcalls import config

log = logging.getLogger("portcalls.ingest")


def port_boxes(ports_csv: Path, buffer_km: float) -> list[tuple[float, float, float, float]]:
    """Return a (min_lat, max_lat, min_lon, max_lon) box around each port."""
    boxes = []
    with open(ports_csv, newline="") as f:
        for row in csv.DictReader(f):
            lat, lon = float(row["lat"]), float(row["lon"])
            reach_km = float(row["radius_km"]) + buffer_km
            dlat = reach_km / 111.0
            dlon = reach_km / (111.0 * math.cos(math.radians(lat)))
            boxes.append((lat - dlat, lat + dlat, lon - dlon, lon + dlon))
    return boxes


def box_filter_sql(boxes) -> str:
    """SQL condition that is true when a point falls inside any port box."""
    return " OR ".join(
        f"(ST_Y(geometry) BETWEEN {a:.6f} AND {b:.6f} "
        f"AND ST_X(geometry) BETWEEN {c:.6f} AND {d:.6f})"
        for a, b, c, d in boxes
    )


def land_day(day: dt.date, source: str | None = None, raw_dir: Path = config.RAW_DIR) -> int:
    """Filter one day of AIS data to port areas and write it as a partition."""
    source = source or config.SOURCE_URL.format(year=day.year, date=day.isoformat())
    final_dir = raw_dir / f"date={day.isoformat()}"
    tmp_dir = raw_dir / f"_tmp_date={day.isoformat()}"

    shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True)
    tmp_file = tmp_dir / "positions.parquet"

    where = box_filter_sql(port_boxes(config.PORTS_SEED, config.INGEST_BUFFER_KM))
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
    log.info("Reading %s", source)
    con.execute(f"""
        COPY (SELECT * FROM read_parquet('{source}') WHERE {where})
        TO '{tmp_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    rows = con.execute(f"SELECT count(*) FROM read_parquet('{tmp_file.as_posix()}')").fetchone()[0]
    con.close()

    # Swap the new partition into place only after the write succeeded.
    if final_dir.exists():
        shutil.rmtree(final_dir)
    tmp_dir.rename(final_dir)
    log.info("Landed %s rows for %s", f"{rows:,}", day)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Land NOAA AIS days into the raw layer.")
    parser.add_argument("--start", required=True, type=dt.date.fromisoformat)
    parser.add_argument("--end", type=dt.date.fromisoformat, help="Defaults to --start")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    day, end = args.start, args.end or args.start
    while day <= end:
        land_day(day)
        day += dt.timedelta(days=1)


if __name__ == "__main__":
    main()
