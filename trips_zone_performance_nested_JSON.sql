/* 3. Zone performance → nested JSON (zone KPIs) */

SELECT
    [zoneId]      = [PULocationID],
    [trips]       = COUNT(*),
    [avgDistance] = ROUND(AVG([trip_distance]), 2),
    [avgFare]     = ROUND(AVG([total_amount]), 2),
    [avgTip]      = ROUND(AVG([tip_amount]), 2)
FROM [dbo].[yellow_tripdata]
GROUP BY [PULocationID]
ORDER BY [trips] DESC
FOR JSON PATH, ROOT('zones');
