# validate_parquet.py
import argparse
from pathlib import Path
import duckdb
import pandas as pd

parser = argparse.ArgumentParser(description="Validate a Parquet file and produce schema/profile/preview reports.")
parser.add_argument("src", help="Path to the Parquet file to validate")
parser.add_argument("--rows", type=int, default=100, help="Number of preview rows to save (default: 100)")
args = parser.parse_args()

# --- normalize path & existence check ---
src_path = Path(args.src).resolve()
if not src_path.exists():
    raise FileNotFoundError(f"File not found: {src_path}")

SRC = str(src_path).replace("\\", "/")  # DuckDB likes forward slashes
PREVIEW_ROWS = args.rows
out_dir = src_path.parent
out_base = out_dir / src_path.stem  # e.g., yellow_tripdata_2024-01

con = duckdb.connect()

# --- 1) Schema (order, names, types) ---
schema_df = con.sql(f"DESCRIBE SELECT * FROM read_parquet('{SRC}')").df()
# schema_df has columns like: column_name, column_type, null, key, default, extra

lines = []
for i, r in schema_df.iterrows():
    lines.append(f"{i:02d}  {r['column_name']}  ::  {r['column_type']}")
schema_path = out_base.with_suffix("").as_posix() + "_schema.txt"
Path(schema_path).write_text("\n".join(lines), encoding="utf-8")

# --- 2) Column profile (nulls, example, min/max for numeric/date/time) ---
numeric_keywords = ["HUGEINT", "BIGINT", "INTEGER", "SMALLINT", "TINYINT",
                    "DOUBLE", "DECIMAL", "REAL", "FLOAT", "UBIGINT", "UINTEGER",
                    "USMALLINT", "UTINYINT"]
ts_keywords = ["TIMESTAMP", "TIMESTAMP_TZ", "DATE", "TIME"]

exprs = []
for _, r in schema_df.iterrows():
    col = r["column_name"]
    typ = str(r["column_type"]).upper()

    # null count + example
    exprs.append(f'SUM("{col}" IS NULL) AS "{col}__nulls"')
    exprs.append(f'MIN(CASE WHEN "{col}" IS NOT NULL THEN CAST("{col}" AS VARCHAR) END) AS "{col}__example"')

    # min/max for numeric or date/time
    if any(k in typ for k in numeric_keywords) or any(k in typ for k in ts_keywords):
        exprs.append(f'MIN("{col}") AS "{col}__min"')
        exprs.append(f'MAX("{col}") AS "{col}__max"')

profile_sql = f"""
WITH src AS (SELECT * FROM read_parquet('{SRC}'))
SELECT
  COUNT(*) AS __rowcount,
  {",\n  ".join(exprs)}
FROM src;
"""

profile_df = con.sql(profile_sql).df().T
profile_df.columns = ["value"]
profile_path = out_base.with_suffix("").as_posix() + "_profile.csv"
profile_df.to_csv(profile_path, encoding="utf-8")

# --- 3) Preview sample (true columns, no wrapping) ---
preview_df = con.sql(f"SELECT * FROM read_parquet('{SRC}') LIMIT {PREVIEW_ROWS}").df()
preview_path = out_base.with_suffix("").as_posix() + "_preview.csv"
preview_df.to_csv(preview_path, index=False, encoding="utf-8")

# --- 4) Rowcount echo ---
rowcount = int(con.sql(f"SELECT COUNT(*) FROM read_parquet('{SRC}')").fetchone()[0])

print("=== DONE ===")
print(f"Schema:  {schema_path}")
print(f"Profile: {profile_path}")
print(f"Preview: {preview_path}")
print(f"Rows:    {rowcount:,}")
