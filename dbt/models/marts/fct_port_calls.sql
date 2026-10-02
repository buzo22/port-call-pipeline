-- One row per port call: a visit in which the vessel actually stopped.
-- Vessels that only pass through a port area are excluded.

with visits as (

    select * from {{ ref('int_port_visits') }}
    where at_rest_hours >= {{ var('min_port_call_at_rest_hours') }}

),

vessels as (

    select * from {{ ref('int_vessels') }}

),

ports as (

    select * from {{ ref('ports') }}

)

select
    visits.visit_id                                                as port_call_id,
    visits.mmsi,
    vessels.imo,
    vessels.vessel_name,
    case
        when visits.vessel_type_code between 70 and 79 then 'cargo'
        when visits.vessel_type_code between 80 and 89 then 'tanker'
    end                                                            as vessel_group,
    vessels.length_m,
    visits.port_code,
    ports.port_name,
    visits.entered_at,
    visits.first_at_rest_at,
    visits.last_at_rest_at,
    visits.exited_at,
    round(epoch(visits.exited_at - visits.entered_at) / 3600.0, 2)       as time_in_port_hours,
    round(visits.at_rest_hours, 2)                                       as at_rest_hours,
    round(epoch(visits.first_at_rest_at - visits.entered_at) / 60.0, 1)  as approach_minutes,
    not (visits.starts_at_window_edge or visits.ends_at_window_edge)     as is_complete,
    visits.position_count
from visits
join vessels on vessels.mmsi = visits.mmsi
join ports   on ports.port_code = visits.port_code
