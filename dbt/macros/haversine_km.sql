{#
  Great-circle distance in kilometres between two points on the Earth,
  using the haversine formula. 6371 km is the Earth's mean radius.
#}
{% macro haversine_km(lat1, lon1, lat2, lon2) -%}
    2 * 6371.0 * asin(sqrt(
        power(sin(radians(({{ lat2 }}) - ({{ lat1 }})) / 2), 2)
        + cos(radians({{ lat1 }})) * cos(radians({{ lat2 }}))
        * power(sin(radians(({{ lon2 }}) - ({{ lon1 }})) / 2), 2)
    ))
{%- endmacro %}
