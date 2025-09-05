USE [nyctaxi];
GO 

SELECT [date] = CAST([tpep_pickup_datetime] AS date) ,
	[trips] = COUNT(*) ,
	[revenue] = ROUND(SUM([total_amount]), 2) ,
	[avg_distance] = ROUND(AVG([trip_distance]), 2) ,
	[avg_minutes] = ROUND(AVG(DATEDIFF(second, [tpep_pickup_datetime], [tpep_dropoff_datetime]))/60.0, 1)
FROM [dbo].[yellow_tripdata]
GROUP BY CAST([tpep_pickup_datetime] AS date)
ORDER BY [date]
FOR JSON PATH, ROOT('daily'), INCLUDE_NULL_VALUES;
GO

