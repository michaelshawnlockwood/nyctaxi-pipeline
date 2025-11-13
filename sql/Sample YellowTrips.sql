-- Works on SQL Server 2012+
SELECT [MonthStart] = DATEFROMPARTS(YEAR(tpep_pickup_datetime), MONTH(tpep_pickup_datetime), 1),
  [Trips] = COUNT_BIG(*)
FROM [dbo].[YellowTrips]
GROUP BY DATEFROMPARTS(YEAR([tpep_pickup_datetime]) ,
	MONTH([tpep_pickup_datetime]), 1)
ORDER BY [MonthStart] ASC;


SELECT TOP (10) PULocationID AS LocationID, COUNT_BIG(*) AS rides
FROM dbo.YellowTrips
WHERE tpep_pickup_datetime >= '2024-01-01' AND tpep_pickup_datetime < '2025-01-01'
  AND PULocationID NOT IN (264,265)
GROUP BY PULocationID
ORDER BY rides DESC;

