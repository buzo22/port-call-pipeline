# Data rules

Findings from exploring one day of NOAA AIS data (2024-01-15, 7.28M rows,
GeoParquet), and the rules the pipeline applies as a result.
Exploration scripts are in `exploration/`.

## Source
- NOAA Marine Cadastre daily GeoParquet, one file per day, already typed.
- Position is stored as a `geometry` point in (longitude, latitude) order.

## Rules

| # | Finding | Rule |
|---|---|---|
| R1 | Position is a geometry point, longitude first | Extract `lon = ST_X(geometry)`, `lat = ST_Y(geometry)` |
| R2 | 185 duplicate (mmsi, timestamp) pairs: 176 exact copies, 9 conflicting | Keep one row per (mmsi, timestamp), chosen deterministically |
| R3 | `imo` is never NULL; missing values are blank strings (58% of rows) | Convert blank strings to NULL for text columns |
| R4 | 210 rows over 50 knots, including tankers at 98.9 kn | Flag implausible speeds as a warning; do not drop, since they only affect pings that were moving |
| R5 | Navigational status lagged the real stop by 13 minutes | Speed (< 0.5 kn) is the primary at-rest signal; status is supporting |
| R6 | Speed flickered across the 0.5 kn threshold while berthing | Define visits by presence in port plus time gaps, not by speed changes |
| R7 | Busiest ships at Los Angeles were stationary all day | Load multiple consecutive days; one day cuts visits at midnight |
| R8 | One ship's ping gaps: median 70 s, p95 184 s, max 30 min | Set the visit gap threshold from fleet-wide gap analysis (Step 5) |

## Scope
- Cargo (vessel type 70-79) and tanker (80-89) vessels.
- Coordinates were all valid in the sample, but the range check stays in place.
