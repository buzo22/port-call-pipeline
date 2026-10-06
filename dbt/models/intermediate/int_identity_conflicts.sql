-- Vessel-days where one MMSI appears to be transmitted from two places at once.
-- Two interleaved, internally consistent tracks produce repeated impossible
-- jumps, while an isolated position spike produces exactly two (out and back).
-- The data cannot tell which track belongs to which ship, so these
-- vessel-days are quarantined rather than guessed at.

select
    mmsi,
    observed_at::date as conflict_date,
    count(*)          as impossible_jumps
from {{ ref('int_positions_despiked') }}
where knots_from_prev > {{ var('max_plausible_speed_knots') }}
group by mmsi, observed_at::date
having count(*) > {{ var('identity_conflict_min_jumps') }}
