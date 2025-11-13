import sys
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
import urllib

server   = r"MSL-LAPTOP\MSSQLSERVER2022"
database = "NycTaxi"
table    = "dbo.TaxiZone"
output   = "nyc_taxi_zones.geojson"

params = urllib.parse.quote_plus(
    f"DRIVER=ODBC Driver 18 for SQL Server;SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;"
)
conn_str = f"mssql+pyodbc:///?odbc_connect={params}"

try:
    print(f"Connecting to SQL Server [{server}] / DB [{database}] ...")
    engine = create_engine(conn_str)
    sql = f"""
        SELECT LocationID, ZoneName, shape.STAsBinary() AS geom
        FROM {table};
    """
    df = pd.read_sql(sql, engine)
    print(f"Retrieved {len(df)} rows from {table}.")
except Exception as e:
    print(f"❌ Database connection or query failed: {e}")
    sys.exit(1)

try:
    print("Converting WKB to GeoDataFrame ...")
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkb(df["geom"]),
        crs="EPSG:4326"  # adjust if necessary
    ).drop(columns=["geom"])
    gdf.to_file(output, driver="GeoJSON")
    print(f"✅ Exported GeoJSON: {output}")
except Exception as e:
    print(f"❌ Export failed: {e}")
    sys.exit(1)
