-- In-scope vessel positions that fall inside a port's radius, tagged with the port.

with positions as (

    select * from {{ ref('stg_ais_positions') }}

),

vessels as (

    select *
    from {{ ref('int_vessels') }}
    where vessel_type_code between {{ var('scope_vessel_type_min') }}
                               and {{ var('scope_vessel_type_max') }}

),

ports as (

    select * from {{ ref('ports') }}

),

in_port as (

    select
        positions.*,
        vessels.vessel_type_code as vessel_type,
        ports.port_code,
        {{ haversine_km('positions.lat', 'positions.lon', 'ports.lat', 'ports.lon') }} as distance_to_port_km
    from positions
    join vessels using (mmsi)
    join ports
      on {{ haversine_km('positions.lat', 'positions.lon', 'ports.lat', 'ports.lon') }} <= ports.radius_km

)

select * from in_port
