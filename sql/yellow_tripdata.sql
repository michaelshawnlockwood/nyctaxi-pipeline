CREATE SCHEMA IF NOT EXISTS bronze;

DROP TABLE IF EXISTS bronze.yellow_tripdata;

CREATE TABLE bronze.yellow_tripdata (
    vendor_id smallint NOT NULL,
    tpep_pickup_datetime timestamp NOT NULL,
    tpep_dropoff_datetime timestamp NOT NULL,
    passenger_count smallint,
    trip_distance numeric(18,4) NOT NULL,
    ratecode_id smallint,
    store_and_fwd_flag varchar(1),
    pu_location_id smallint NOT NULL,
    do_location_id smallint NOT NULL,
    payment_type smallint NOT NULL,
    fare_amount numeric(18,4) NOT NULL,
    extra numeric(18,4) NOT NULL,
    mta_tax numeric(18,4) NOT NULL,
    tip_amount numeric(18,4) NOT NULL,
    tolls_amount numeric(18,4) NOT NULL,
    improvement_surcharge numeric(18,4) NOT NULL,
    total_amount numeric(18,4) NOT NULL,
    congestion_surcharge numeric(18,4),
    airport_fee numeric(18,4)
);