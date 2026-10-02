-- A vessel cannot be in two visits at the same time, in the same port or different ports.
select a.visit_id, b.visit_id as overlapping_visit_id
from {{ ref('int_port_visits') }} a
join {{ ref('int_port_visits') }} b
  on a.mmsi = b.mmsi
 and a.visit_id < b.visit_id
 and a.entered_at < b.exited_at
 and b.entered_at < a.exited_at
