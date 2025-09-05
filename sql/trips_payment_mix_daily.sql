/* 2. Payment mix daily → nested JSON*/

SET STATISTICS IO, TIME ON;
GO

WITH [days] AS (
    SELECT [date] = CAST([tpep_pickup_datetime] AS date)
    FROM [dbo].[yellow_tripdata]
    GROUP BY CAST([tpep_pickup_datetime] AS date)
),
[methods] AS (
    SELECT
        [date]      = CAST([tpep_pickup_datetime] AS date),
        [payMethod] = CASE [payment_type]
                        WHEN 1 THEN 'credit'
                        WHEN 2 THEN 'cash'
                        WHEN 3 THEN 'no_charge'
                        WHEN 4 THEN 'dispute'
                        WHEN 5 THEN 'unknown'
                        WHEN 6 THEN 'voided'
                        ELSE 'other'
                      END,
        [trips]     = COUNT(*)
    FROM [dbo].[yellow_tripdata]
    GROUP BY CAST([tpep_pickup_datetime] AS date), [payment_type]
)
SELECT
    [date]       = [d].[date],
    [paymentMix] = JSON_QUERY(
                      (
                        SELECT
                            [method] = [m].[payMethod],
                            [trips]  = [m].[trips]
                        FROM [methods] AS [m]
                        WHERE [m].[date] = [d].[date]
                        FOR JSON PATH
                      )
                   )
FROM [days] AS [d]
ORDER BY [d].[date]
FOR JSON PATH, ROOT('paymentByDay');
