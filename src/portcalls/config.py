"""Central configuration: paths, source location and ingest settings."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "ais"
PORTS_SEED = PROJECT_ROOT / "dbt" / "seeds" / "ports.csv"

SOURCE_URL = (
    "https://ocmgeodatastor1.blob.core.windows.net/marinecadastre/"
    "ais{year}/ais-{date}.parquet"
)

# Margin around each port radius so approach and departure pings are kept.
INGEST_BUFFER_KM = 10
