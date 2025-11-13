SET NOCOUNT ON;
GO

CREATE OR ALTER FUNCTION dbo.fn_TaxiZonePointsByQuadrant
(
  @quadrant sysname = N'NE',
  @top int = 0,
  @tolerance float = 0.1
)
RETURNS TABLE
AS
RETURN
WITH src AS (
  SELECT
    tz.LocationID,
    tz.Borough,
    tz.Zone,
    tz.shape,
    ROW_NUMBER() OVER (ORDER BY tz.LocationID) AS rn
  FROM dbo.TaxiZones AS tz
),
base AS (
  SELECT TOP (@top)
    s.LocationID,
    s.Borough,
    s.Zone,
    CASE WHEN @tolerance IS NULL OR @tolerance <= 0 THEN s.shape ELSE s.shape.Reduce(@tolerance) END AS shape,
    s.shape.STNumGeometries() AS ngeom
  FROM src AS s
),
geoms AS (
  SELECT
    b.LocationID,
    b.Borough,
    b.Zone,
    g.geom_id,
    b.shape.STGeometryN(g.geom_id) AS geom
  FROM base AS b
  CROSS APPLY (
    SELECT TOP (b.ngeom) ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS geom_id
    FROM sys.all_objects
  ) AS g
),
rings AS (
  SELECT
    g.LocationID,
    g.Borough,
    g.Zone,
    g.geom_id,
    r.ring_id,
    g.geom.RingN(r.ring_id) AS ring
  FROM geoms AS g
  CROSS APPLY (
    SELECT TOP (g.geom.NumRings()) ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS ring_id
    FROM sys.all_objects
  ) AS r
),
pts AS (
  SELECT
    r.LocationID,
    r.Borough,
    r.Zone,
    r.geom_id,
    r.ring_id,
    p.pt_id,
    r.ring.STPointN(p.pt_id) AS pt
  FROM rings AS r
  CROSS APPLY (
    SELECT TOP (r.ring.STNumPoints()) ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS pt_id
    FROM sys.all_objects
  ) AS p
),
zone_centroids AS (
  SELECT
    LocationID,
    AVG(CAST(pt.Long AS DECIMAL(18,12))) AS cx,
    AVG(CAST(pt.Lat  AS DECIMAL(18,12))) AS cy
  FROM pts
  GROUP BY LocationID
),
global_center AS (
  SELECT
    AVG(cx) AS centerX,
    AVG(cy) AS centerY
  FROM zone_centroids
),
labeled AS (
  SELECT
    zc.LocationID,
    CASE
      WHEN zc.cx >= gc.centerX AND zc.cy >= gc.centerY THEN N'NE'
      WHEN zc.cx <  gc.centerX AND zc.cy >= gc.centerY THEN N'NW'
      WHEN zc.cx >= gc.centerX AND zc.cy <  gc.centerY THEN N'SE'
      ELSE N'SW'
    END AS quadrant
  FROM zone_centroids AS zc
  CROSS JOIN global_center AS gc
),
filtered_pts AS (
  SELECT
    p.LocationID,
    p.Borough,
    p.Zone,
    p.geom_id,
    p.ring_id,
    p.pt_id,
    p.pt
  FROM pts AS p
  INNER JOIN labeled AS l
    ON l.LocationID = p.LocationID
  WHERE UPPER(@quadrant) = N'ALL' OR l.quadrant = UPPER(@quadrant)
)
SELECT
  LocationID,
  Borough,
  Zone,
  geom_id,
  ring_id,
  pt_id,
  CAST(pt.Long AS DECIMAL(18,12)) AS lon,
  CAST(pt.Lat  AS DECIMAL(18,12)) AS lat
FROM filtered_pts;
GO

CREATE OR ALTER PROCEDURE [dbo].[pr_GetTaxiZonePoints]
  @quadrant sysname = N'NE',
  @top int = 0,
  @tolerance float = 0.1
AS
BEGIN
  SET NOCOUNT ON;
  SELECT
    LocationID,
    Borough,
    Zone,
    geom_id,
    ring_id,
    pt_id,
    lon,
    lat
  FROM dbo.fn_TaxiZonePointsByQuadrant(@quadrant, @top, @tolerance)
  ORDER BY LocationID, geom_id, ring_id, pt_id;
END
GO

SET NOCOUNT OFF;
EXEC [dbo].[pr_GetTaxiZonePoints] @quadrant = 'NE' ,
	@top = 100 ,
	@tolerance = 0.1