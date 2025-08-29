IF OBJECT_ID(N'[dbo].[yellow_tripdata]', N'U') IS NOT NULL
    DROP TABLE [dbo].[yellow_tripdata];
GO

CREATE TABLE [dbo].[yellow_tripdata] (
    [VendorID] TINYINT NOT NULL,
    [tpep_pickup_datetime] DATETIME2 NOT NULL,
    [tpep_dropoff_datetime] DATETIME2 NOT NULL,
    [passenger_count] TINYINT NULL,
    [trip_distance] DECIMAL(18,4) NOT NULL,
    [RatecodeID] TINYINT NULL,
    [store_and_fwd_flag] VARCHAR(1) NULL,
    [PULocationID] SMALLINT NOT NULL,
    [DOLocationID] SMALLINT NOT NULL,
    [payment_type] TINYINT NOT NULL,
    [fare_amount] DECIMAL(18,4) NOT NULL,
    [extra] DECIMAL(18,4) NOT NULL,
    [mta_tax] DECIMAL(18,4) NOT NULL,
    [tip_amount] DECIMAL(18,4) NOT NULL,
    [tolls_amount] DECIMAL(18,4) NOT NULL,
    [improvement_surcharge] DECIMAL(18,4) NOT NULL,
    [total_amount] DECIMAL(18,4) NOT NULL,
    [congestion_surcharge] DECIMAL(18,4) NULL,
    [Airport_fee] DECIMAL(18,4) NULL
);
GO
