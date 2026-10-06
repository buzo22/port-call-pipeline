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
| R10 | Regional feed outage on 2024-01-14, ~10:30-20:00 UTC: Houston and Savannah report zero pings while other ports are normal | Pending: visits must not be split by, or treated as complete next to, a feed outage |
| R11 | Isolated pings ~1,000 km from a vessel's track, unreachable at <= 60 kn from both neighbours | Flag as position spikes and exclude (49 of 2.0M positions, 12 vessels) |
| R12 | MMSI 636093156 transmitted two coherent, interleaved tracks (Savannah and New York) on the same days | Vessel-days with more than 4 impossible jumps are identity conflicts; touching visits are quarantined and excluded from port calls |

## Scope
- Cargo (vessel type 70-79) and tanker (80-89) vessels.
- Coordinates were all valid in the sample, but the range check stays in place.


