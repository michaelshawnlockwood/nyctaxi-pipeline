DECLARE @from datetime2 = '2024-01-01';
DECLARE @to   datetime2 = '2025-01-01';

;WITH counts AS (
  SELECT CAST(PULocationID AS int) AS LocationID, COUNT_BIG(*) AS [count]
  FROM dbo.YellowTrips
  WHERE tpep_pickup_datetime >= @from
    AND tpep_pickup_datetime <  @to
    AND PULocationID NOT IN (264,265)
  GROUP BY PULocationID
)
SELECT
  meta = JSON_QUERY((
    SELECT 'pickups' AS metric,
           CONVERT(char(10), @from, 23) AS period_start,
           CONVERT(char(10), @to,   23) AS period_end
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)),
  data = JSON_QUERY((
    SELECT z.LocationID, COALESCE(c.[count], 0) AS [count]
    FROM dbo.TaxiZoneLookup AS z
    LEFT JOIN counts AS c ON c.LocationID = z.LocationID
    ORDER BY [count] DESC
    FOR JSON PATH))
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
