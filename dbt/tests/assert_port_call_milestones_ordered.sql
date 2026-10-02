-- Milestones must happen in order: enter, first stop, last stop, exit.
select *
from {{ ref('fct_port_calls') }}
where not (entered_at <= first_at_rest_at
       and first_at_rest_at <= last_at_rest_at
       and last_at_rest_at <= exited_at)
