-- 8a) Count + validity
SELECT COUNT(*) AS rows_loaded,
       SUM(CASE WHEN shape.STIsValid() = 1 THEN 1 ELSE 0 END) AS valid_geographies
FROM dbo.TaxiZones;

-- 8b) SRID must be 4326
SELECT shape.STSrid AS srid, COUNT(*) AS n
FROM dbo.TaxiZones
GROUP BY shape.STSrid;

-- 8c) Quick centroid glance (lon/lat around -74 / 40.7)
SELECT TOP (12)
  LocationID, Zone,
  shape.EnvelopeCenter().Long AS lon,
  shape.EnvelopeCenter().Lat  AS lat
FROM dbo.TaxiZones
ORDER BY LocationID;
