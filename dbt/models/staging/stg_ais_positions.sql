-- One clean row per vessel per timestamp.
-- Implements data rules R1-R4 (docs/data-rules.md).

with source as (

    select * from {{ source('ais', 'positions') }}

),

renamed as (

    select
        mmsi,
        base_date_time                  as observed_at,
        ST_Y(geometry)                  as lat,            -- R1: latitude is Y
        ST_X(geometry)                  as lon,            -- R1: longitude is X
        sog                             as sog_knots,
        cog                             as cog_deg,
        heading                         as heading_deg,
        nullif(trim(vessel_name), '')   as vessel_name,    -- R3: blank to NULL
        nullif(trim(imo), '')           as imo,            -- R3
        nullif(trim(call_sign), '')     as call_sign,      -- R3
        vessel_type                     as vessel_type_code,
        status                          as nav_status_code,
        length                          as length_m,
        width                           as width_m,
        draft                           as draft_m,
        transceiver                     as transceiver_class,
        sog > 50                        as is_implausible_speed,  -- R4: flag, don't drop
        date                            as source_date
    from source
    where mmsi is not null
      and base_date_time is not null
      and geometry is not null

),

valid as (

    select *
    from renamed
    where lat between -90 and 90
      and lon between -180 and 180

)

-- R2: one row per (mmsi, observed_at). The ORDER BY makes the choice
-- deterministic, so reruns always keep the same row for conflicting duplicates.
select *
from valid
qualify row_number() over (
    partition by mmsi, observed_at
    order by sog_knots nulls last, nav_status_code nulls last, lat, lon, source_date
) = 1
