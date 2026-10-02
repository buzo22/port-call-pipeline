-- Port circles must not overlap, otherwise one ping could match two ports
-- and be counted twice.
select a.port_code, b.port_code as overlapping_port_code
from {{ ref('ports') }} a
join {{ ref('ports') }} b
  on a.port_code < b.port_code
 and {{ haversine_km('a.lat', 'a.lon', 'b.lat', 'b.lon') }} < a.radius_km + b.radius_km
