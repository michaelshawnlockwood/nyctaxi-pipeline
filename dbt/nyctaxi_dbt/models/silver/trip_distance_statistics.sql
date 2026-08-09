{{ config(materialized='view') }}

select
    count(*) as trip_count,
    min(trip_distance) as min_distance,
    avg(trip_distance) as mean_distance,

    percentile_cont(0.5)
        within group (order by trip_distance) as median_distance,

    stddev_samp(trip_distance) as stddev_distance,

    avg(trip_distance) - stddev_samp(trip_distance)
        as minus_1_stddev,

    avg(trip_distance) + stddev_samp(trip_distance)
        as plus_1_stddev,

    avg(trip_distance) - (2 * stddev_samp(trip_distance))
        as minus_2_stddev,

    avg(trip_distance) + (2 * stddev_samp(trip_distance))
        as plus_2_stddev,

    max(trip_distance) as max_distance

from {{ ref('silver_yellow_tripdata') }}