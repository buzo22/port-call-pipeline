-- In-scope vessel positions inside a port's radius, tagged with the port.
-- Position spikes are excluded (see int_positions_despiked).

with positions as (

    select p.*, v.vessel_type_code as vessel_type
    from {{ ref('int_positions_despiked') }} p
    join {{ ref('int_vessels') }} v on v.mmsi = p.mmsi
    where not p.is_position_spike

),

ports as (

    select * from {{ ref('ports') }}

)

select
    positions.*,
    ports.port_code,
    {{ haversine_km('positions.lat', 'positions.lon', 'ports.lat', 'ports.lon') }} as distance_to_port_km
from positions
join ports
  on {{ haversine_km('positions.lat', 'positions.lon', 'ports.lat', 'ports.lon') }} <= ports.radius_km
