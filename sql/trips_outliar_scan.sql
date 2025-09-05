/* Outlier scan → JSON (flag suspicious trips) */

WITH [base] AS (
    SELECT [date]         = CAST([tpep_pickup_datetime] AS date),
           [tripDistance] = [trip_distance],
           [minutes]      = DATEDIFF(minute, [tpep_pickup_datetime], [tpep_dropoff_datetime]),
           [totalAmount]  = [total_amount],
           [puLocationId] = [PULocationID],
           [doLocationId] = [DOLocationID]
    FROM   [dbo].[yellow_tripdata]
),
[scored] AS (
    SELECT *,
           [badTimeOrDist] = IIF([minutes] <= 0 OR [tripDistance] < 0.1, 1, 0),
           [fareOutlier]   = IIF([totalAmount] < 0 OR [totalAmount] > 500, 1, 0)
    FROM   [base]
)
SELECT TOP (200)
       [date],
       [puLocationId],
       [doLocationId],
       [tripDistance],
       [minutes],
       [totalAmount],
       [outlier] = IIF([badTimeOrDist] = 1 OR [fareOutlier] = 1, 1, 0)
FROM   [scored]
WHERE  [badTimeOrDist] = 1
    OR [fareOutlier] = 1
ORDER BY [date] DESC
FOR JSON PATH, ROOT('outliers');
