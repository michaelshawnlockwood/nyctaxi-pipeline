USE [nyctaxi];
GO 

DECLARE @daily nvarchar(max);
DECLARE @zones nvarchar(max);

SET @daily = (
    SELECT [date]    = CAST([tpep_pickup_datetime] AS date),
           [trips]   = COUNT(*),
           [revenue] = ROUND(SUM([total_amount]), 2)
    FROM   [dbo].[yellow_tripdata]
    GROUP BY CAST([tpep_pickup_datetime] AS date)
    ORDER BY [date]
    FOR JSON PATH
);

SET @zones = (
    SELECT [zoneId]      = [PULocationID],
           [trips]       = COUNT(*),
           [avgFare]     = ROUND(AVG([total_amount]), 2),
           [avgDistance] = ROUND(AVG([trip_distance]), 2)
    FROM   [dbo].[yellow_tripdata]
    GROUP BY [PULocationID]
    ORDER BY [trips] DESC
    FOR JSON PATH
);

SELECT [generatedAtUtc] = SYSUTCDATETIME(),
       [daily]          = JSON_QUERY(@daily),
       [zones]          = JSON_QUERY(@zones)
FOR JSON PATH, ROOT('nycTaxiPayload');
