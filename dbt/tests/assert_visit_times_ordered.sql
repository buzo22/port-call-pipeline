-- A visit cannot end before it starts, and at-rest time cannot exceed time in port.
select *
from {{ ref('int_port_visits') }}
where exited_at < entered_at
   or at_rest_hours > epoch(exited_at - entered_at) / 3600.0 + 0.01
