-- One row per vessel with its best-known attributes.
-- Static fields such as vessel type are missing on some pings, so each
-- vessel takes the most common non-null value across all of its pings.

select
    mmsi,
    mode(vessel_type_code) filter (where vessel_type_code is not null) as vessel_type_code,
    mode(vessel_name)      filter (where vessel_name is not null)      as vessel_name,
    mode(imo)              filter (where imo is not null)              as imo,
    max(length_m)                                                      as length_m,
    count(*)                                                           as ping_count
from {{ ref('stg_ais_positions') }}
group by mmsi
