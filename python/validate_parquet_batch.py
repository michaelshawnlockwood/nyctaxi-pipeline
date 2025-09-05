# validate_parquet_batch.py
import argparse
from pathlib import Path
import duckdb
import pandas as pd
import traceback

from typing import List, Tuple

def validate_one(src_path: Path, rows: int, con: duckdb.DuckDBPyConnection, skip_existing: bool) -> Tuple[str, int, str]:
    """
    Returns (file, rowcount, status) where status is 'OK' or the error message.
    """
    try:
        src_path = src_path.resolve()
        if not src_path.exists():
            return (str(src_path), 0, "NOT_FOUND")

        # Output base next to the source file
        out_base = src_path.parent / src_path.stem
        schema_path  = Path(out_base.as_posix() + "_schema.txt")
        profile_path = Path(out_base.as_posix() + "_profile.csv")
        preview_path = Path(out_base.as_posix() + "_preview.csv")

        if skip_existing and schema_path.exists() and profile_path.exists() and preview_path.exists():
            # Still report rowcount to the summary
            rowcount = int(con.sql(f"SELECT COUNT(*) FROM read_parquet('{str(src_path).replace('\\','/')}')").fetchone()[0])
            return (str(src_path), rowcount, "SKIPPED_EXISTS")

        SRC = str(src_path).replace("\\", "/")

        # 1) Schema
        schema_df = con.sql(f"DESCRIBE SELECT * FROM read_parquet('{SRC}')").df()
        lines = [f"{i:02d}  {r['column_name']}  ::  {r['column_type']}" for i, r in schema_df.iterrows()]
        schema_path.write_text("\n".join(lines), encoding="utf-8")

        # 2) Profile
        numeric_keywords = ["HUGEINT", "BIGINT", "INTEGER", "SMALLINT", "TINYINT",
                            "DOUBLE", "DECIMAL", "REAL", "FLOAT", "UBIGINT", "UINTEGER",
                            "USMALLINT", "UTINYINT"]
        ts_keywords = ["TIMESTAMP", "TIMESTAMP_TZ", "DATE", "TIME"]

        exprs = []
        for _, r in schema_df.iterrows():
            col = r["column_name"]
            typ = str(r["column_type"]).upper()
            exprs.append(f'SUM("{col}" IS NULL) AS "{col}__nulls"')
            exprs.append(f'MIN(CASE WHEN "{col}" IS NOT NULL THEN CAST("{col}" AS VARCHAR) END) AS "{col}__example"')
            if any(k in typ for k in numeric_keywords) or any(k in typ for k in ts_keywords):
                exprs.append(f'MIN("{col}") AS "{col}__min"')
                exprs.append(f'MAX("{col}") AS "{col}__max"')

        profile_sql = f"""
        WITH src AS (SELECT * FROM read_parquet('{SRC}'))
        SELECT
          COUNT(*) AS __rowcount,
          {", ".join(exprs)}
        FROM src;
        """
        profile_df = con.sql(profile_sql).df().T
        profile_df.columns = ["value"]
        profile_df.to_csv(profile_path, encoding="utf-8")

        # 3) Preview
        preview_df = con.sql(f"SELECT * FROM read_parquet('{SRC}') LIMIT {rows}").df()
        preview_df.to_csv(preview_path, index=False, encoding="utf-8")

        # 4) Rowcount
        rowcount = int(con.sql(f"SELECT COUNT(*) FROM read_parquet('{SRC}')").fetchone()[0])
        return (str(src_path), rowcount, "OK")
    except Exception as e:
        return (str(src_path), 0, f"ERROR: {e}")

def main():
    p = argparse.ArgumentParser(description="Validate all Parquet files in a folder (or a single file).")
    p.add_argument("src", help="Folder or file path")
    p.add_argument("--pattern", default="*.parquet", help="Glob pattern when src is a folder (default: *.parquet)")
    p.add_argument("--rows", type=int, default=100, help="Preview rows to save (default: 100)")
    p.add_argument("--recursive", action="store_true", help="Recurse into subfolders")
    p.add_argument("--skip-existing", action="store_true", help="Skip files whose schema/profile/preview already exist")
    args = p.parse_args()

    src_path = Path(args.src).resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"Not found: {src_path}")

    # Build file list
    if src_path.is_file():
        files = [src_path]
    else:
        if args.recursive:
            files = sorted(src_path.rglob(args.pattern))
        else:
            files = sorted(src_path.glob(args.pattern))

    if not files:
        print("No files matched.")
        return

    con = duckdb.connect()
    results: List[Tuple[str, int, str]] = []

    print(f"Validating {len(files)} file(s)...")
    for f in files:
        file_str = str(f)
        print(f"-> {file_str}")
        res = validate_one(f, args.rows, con, args.skip_existing)
        results.append(res)
        print(f"   {res[2]}  rows={res[1]}")

    # Write summary next to the input root (or next to the file)
    out_root = src_path.parent if src_path.is_file() else src_path
    summary_csv = out_root / "validation_summary.csv"
    df = pd.DataFrame(results, columns=["file", "rows", "status"])
    df.to_csv(summary_csv, index=False, encoding="utf-8")

    print("\n=== SUMMARY ===")
    print(f"Total files: {len(results)}")
    print(f"OK:         {(df['status'] == 'OK').sum()}")
    print(f"Skipped:    {(df['status'] == 'SKIPPED_EXISTS').sum()}")
    print(f"Errors:     {(df['status'].str.startswith('ERROR')).sum()}")
    print(f"Summary:    {summary_csv}")

if __name__ == "__main__":
    main()
