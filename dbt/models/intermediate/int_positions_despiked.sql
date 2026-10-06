-- In-scope vessel positions, with position spikes flagged.
-- A spike is a ping that is physically unreachable from BOTH its previous
-- and its next ping: the vessel would have to jump away and straight back.
-- Requiring both sides keeps genuine jumps, such as a vessel reappearing
-- after a data gap, which are unreachable from one side only.

with positions as (

    select p.*
    from {{ ref('stg_ais_positions') }} p
    join {{ ref('int_vessels') }} v on v.mmsi = p.mmsi
    where v.vessel_type_code between {{ var('scope_vessel_type_min') }}
                                 and {{ var('scope_vessel_type_max') }}

),

neighbours as (

    select
        *,
        lag(lat) over w          as prev_lat,
        lag(lon) over w          as prev_lon,
        lag(observed_at) over w  as prev_at,
        lead(lat) over w         as next_lat,
        lead(lon) over w         as next_lon,
        lead(observed_at) over w as next_at
    from positions
    window w as (partition by mmsi order by observed_at)

),

speeds as (

    -- Implied speed in knots: km / 1.852 gives nautical miles, divided by hours.
    select
        *,
        {{ haversine_km('prev_lat', 'prev_lon', 'lat', 'lon') }} / 1.852
            / nullif(epoch(observed_at - prev_at) / 3600.0, 0)    as knots_from_prev,
        {{ haversine_km('lat', 'lon', 'next_lat', 'next_lon') }} / 1.852
            / nullif(epoch(next_at - observed_at) / 3600.0, 0)    as knots_to_next
    from neighbours

)

select
    * exclude (prev_lat, prev_lon, prev_at, next_lat, next_lon, next_at),
    coalesce(
        knots_from_prev > {{ var('max_plausible_speed_knots') }}
        and knots_to_next > {{ var('max_plausible_speed_knots') }},
        false
    ) as is_position_spike
from speeds
