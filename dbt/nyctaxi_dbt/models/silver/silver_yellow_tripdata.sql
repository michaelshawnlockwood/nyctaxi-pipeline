{{ config(materialized='view') }}

select
    *,
    case
        when trip_distance < 0.25 then 'extreme_short'
        when trip_distance < 1 then 'very_short'
        when trip_distance < 3 then 'short'
        when trip_distance < 7 then 'medium'
        when trip_distance < 15 then 'long'
        when trip_distance < 50 then 'very_long'
        else 'extreme_long'
    end as trip_distance_class

from {{ source('bronze', 'yellow_tripdata') }}