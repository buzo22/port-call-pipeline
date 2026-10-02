-- Groups each vessel's in-port pings into visits ("gaps and islands").
-- A new visit starts when the gap since the vessel's previous ping in the
-- same port exceeds visit_max_gap_hours (rule R6: visits are defined by
-- presence and time gaps, not by speed changes).

{% set max_gap_seconds = var('visit_max_gap_hours') * 3600 %}

with positions as (

    select * from {{ ref('int_port_positions') }}

),

window_bounds as (

    -- The time span of the loaded data, used to flag visits cut off at its edges (rule R7).
    select min(observed_at) as data_start, max(observed_at) as data_end
    from {{ ref('stg_ais_positions') }}

),

sequenced as (

    -- Step 1: time since the previous ping and until the next one.
    select
        *,
        epoch(observed_at - lag(observed_at) over w)  as seconds_since_prev,
        epoch(lead(observed_at) over w - observed_at) as seconds_to_next
    from positions
    window w as (partition by mmsi, port_code order by observed_at)

),

numbered as (

    -- Steps 2 and 3: mark visit starts, then number visits with a running total.
    select
        *,
        sum(case when seconds_since_prev is null or seconds_since_prev > {{ max_gap_seconds }}
                 then 1 else 0 end)
            over (partition by mmsi, port_code order by observed_at
                  rows between unbounded preceding and current row) as visit_seq
    from sequenced

),

visits as (

    select
        mmsi,
        port_code,
        visit_seq,
        min(observed_at)  as entered_at,
        max(observed_at)  as exited_at,
        count(*)          as position_count,
        -- At-rest time: intervals that start on an at-rest ping and stay within the visit.
        sum(case when sog_knots < {{ var('at_rest_sog_knots') }}
                  and seconds_to_next <= {{ max_gap_seconds }}
                 then seconds_to_next else 0 end) / 3600.0 as at_rest_hours,
                 min(observed_at) filter (where sog_knots < {{ var('at_rest_sog_knots') }}) as first_at_rest_at,
                 max(observed_at) filter (where sog_knots < {{ var('at_rest_sog_knots') }}) as last_at_rest_at,
        max(vessel_type)  as vessel_type_code
    from numbered
    group by mmsi, port_code, visit_seq

)

select
    md5(concat_ws('|', mmsi, port_code, entered_at))                           as visit_id,
    visits.*,
    entered_at <= data_start + to_hours({{ var('visit_max_gap_hours') }})     as starts_at_window_edge,
    exited_at  >= data_end   - to_hours({{ var('visit_max_gap_hours') }})     as ends_at_window_edge
from visits
cross join window_bounds
