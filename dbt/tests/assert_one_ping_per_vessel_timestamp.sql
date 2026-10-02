-- Rule R2: staging must contain at most one row per vessel per timestamp.
-- A test passes when this query returns zero rows.
select mmsi, observed_at, count(*) as n
from {{ ref('stg_ais_positions') }}
group by mmsi, observed_at
having count(*) > 1
