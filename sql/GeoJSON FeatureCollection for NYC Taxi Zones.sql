-- GeoJSON FeatureCollection for NYC Taxi Zones
-- Assumes: dbo.TaxiZones(LocationID int, Borough nvarchar(50), Zone nvarchar(80), shape geography SRID 4326)

-- 1) Safety checks (optional but recommended)
IF EXISTS (SELECT 1 FROM sys.columns c
           JOIN sys.types t ON c.user_type_id = t.user_type_id
           WHERE c.object_id = OBJECT_ID('dbo.TaxiZones')
             AND c.name = 'shape'
             AND t.name <> 'geography')
BEGIN
  THROW 50001, 'dbo.TaxiZones.shape must be GEOGRAPHY (SRID 4326).', 1;
END;

IF EXISTS (SELECT 1 FROM dbo.TaxiZones WHERE shape.STSrid <> 4326)
BEGIN
  THROW 50002, 'All geometries must use SRID 4326 (WGS84). Re-load/reproject before exporting.', 1;
END;

-- 2) Build Feature array
;WITH g AS (
  SELECT
    tz.LocationID,
    tz.Borough,
    tz.Zone,
    -- ReorientObject() nudges ring orientation to right-hand rule (helpful for GeoJSON viewers)
    tz.shape.ReorientObject() AS gshape,
    tz.shape.STGeometryType() AS gtype
  FROM dbo.TaxiZones AS tz
),
-- Expand MultiPolygon/Polygon into per-polygon records
poly AS (
  SELECT
    g.LocationID, g.Borough, g.Zone,
    CASE 
      WHEN g.gtype = 'MultiPolygon' THEN g.gshape.STGeometryN(n)
      WHEN g.gtype = 'Polygon'      THEN g.gshape
      ELSE NULL
    END AS polygeom
  FROM g
  CROSS APPLY (
    SELECT TOP (CASE WHEN g.gtype='MultiPolygon' THEN g.gshape.STNumGeometries() ELSE 1 END)
           ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS n
    FROM sys.all_objects -- cheap row source
  ) AS N
  WHERE g.gtype IN ('Polygon','MultiPolygon')
),
-- For each polygon, emit its rings (exterior + holes)
rings AS (
  SELECT
    p.LocationID, p.Borough, p.Zone,
    p.polygeom,
    r.ringIndex,
    p.polygeom.RingN(r.ringIndex) AS ringgeom
  FROM poly AS p
  CROSS APPLY (
    SELECT TOP (p.polygeom.STNumRings())
           ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS ringIndex
    FROM sys.all_objects
  ) AS r
),
-- For each ring, list its points as [lon, lat]
ring_coords AS (
  SELECT
    r.LocationID, r.Borough, r.Zone,
    r.ringIndex,
    pts.ptOrder,
    JSON_QUERY(CONCAT('[', 
      CAST(r.ringgeom.STPointN(pts.ptOrder).Long AS varchar(38)), ',', 
      CAST(r.ringgeom.STPointN(pts.ptOrder).Lat  AS varchar(38)), ']'
    )) AS coord
  FROM rings AS r
  CROSS APPLY (
    SELECT TOP (r.ringgeom.STNumPoints())
           ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS ptOrder
    FROM sys.all_objects
  ) AS pts
),
-- Pack each ring into [[lon,lat], ...]
rings_json AS (
  SELECT
    LocationID, Borough, Zone, ringIndex,
    JSON_QUERY((
      SELECT coord
      FROM ring_coords rc
      WHERE rc.LocationID = r.LocationID
        AND rc.Borough    = r.Borough
        AND rc.Zone       = r.Zone
        AND rc.ringIndex  = r.ringIndex
      ORDER BY rc.ptOrder
      FOR JSON PATH
    )) AS ringArray
  FROM rings r
  GROUP BY LocationID, Borough, Zone, ringIndex
),
-- Pack polygon coordinates into [[[...ring1...],[...hole...], ...]]
poly_json AS (
  SELECT
    p.LocationID, p.Borough, p.Zone,
    JSON_QUERY((
      SELECT ringArray
      FROM rings_json rj
      WHERE rj.LocationID = p.LocationID
        AND rj.Borough    = p.Borough
        AND rj.Zone       = p.Zone
      ORDER BY rj.ringIndex
      FOR JSON PATH
    )) AS polygonCoords
  FROM poly p
  GROUP BY p.LocationID, p.Borough, p.Zone
),
-- Group polygons per feature: MultiPolygon uses "MultiPolygon" with multiple polygon coordinate arrays,
-- Polygon still works as MultiPolygon with single polygon array for simplicity/consistency.
feature_geoms AS (
  SELECT
    LocationID, Borough, Zone,
    JSON_QUERY((
      SELECT 
        CASE WHEN COUNT(*) > 1 THEN 'MultiPolygon' ELSE 'Polygon' END AS [type],
        CASE WHEN COUNT(*) > 1 
             THEN JSON_QUERY((
                    SELECT polygonCoords
                    FROM poly_json pp
                    WHERE pp.LocationID = fg.LocationID
                      AND pp.Borough    = fg.Borough
                      AND pp.Zone       = fg.Zone
                    FOR JSON PATH
                  ))
             ELSE JSON_QUERY((SELECT TOP(1) polygonCoords FROM poly_json pp
                               WHERE pp.LocationID = fg.LocationID
                                 AND pp.Borough    = fg.Borough
                                 AND pp.Zone       = fg.Zone))
        END AS coordinates
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    )) AS geometry
  FROM poly_json fg
  GROUP BY LocationID, Borough, Zone
),
-- Final Feature objects
features AS (
  SELECT
    JSON_QUERY((
      SELECT
        'Feature' AS [type],
        fg.geometry AS [geometry],
        -- properties
        (SELECT 
           LocationID, 
           Borough, 
           Zone
         FOR JSON PATH, WITHOUT_ARRAY_WRAPPER) AS [properties]
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    )) AS feature
  FROM feature_geoms fg
)
-- 3) Wrap as FeatureCollection
SELECT JSON_QUERY((
  SELECT 
    'FeatureCollection' AS [type],
    JSON_QUERY((
      SELECT feature
      FROM features
      FOR JSON PATH
    )) AS [features]
  FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
)) AS GeoJSON;
