# validate_psv_batch.py
import argparse
from pathlib import Path
import duckdb
import pandas as pd

def validate_one(con, src: Path, rows: int):
    SRC = str(src).replace("\\", "/")
    out_base = src.with_suffix("")

    READ = f"read_csv('{SRC}', delim='|', header=True, quote='\"', escape='\"')"

    # Schema
    schema_df = con.sql(f"DESCRIBE SELECT * FROM {READ}").df()
    schema_path = out_base.as_posix() + "_schema.txt"
    lines = [f"{i:02d}  {r['column_name']}  ::  {r['column_type']}" for i, r in schema_df.iterrows()]
    Path(schema_path).write_text("\n".join(lines), encoding="utf-8")

    # Profile
    exprs = []
    for _, r in schema_df.iterrows():
        col = r["column_name"]
        typ = str(r["column_type"]).upper()
        exprs.append(f"SUM(({col} IS NULL) OR CAST({col} AS VARCHAR)='') AS {col}__nulls")
        exprs.append(f"MIN(NULLIF(CAST({col} AS VARCHAR), '')) AS {col}__example")
        if any(k in typ for k in ["INT", "REAL", "DECIMAL", "DOUBLE", "FLOAT", "DATE", "TIME", "TIMESTAMP"]):
            exprs.append(f"MIN({col}) AS {col}__min")
            exprs.append(f"MAX({col}) AS {col}__max")

    profile_sql = f"""
    WITH src AS (SELECT * FROM {READ})
    SELECT {", ".join(exprs)} FROM src
    """
    profile_df = con.sql(profile_sql).df().T
    profile_df.columns = ["value"]
    profile_path = out_base.as_posix() + "_profile.csv"
    profile_df.to_csv(profile_path, encoding="utf-8")

    # Preview
    preview_df = con.sql(f"SELECT * FROM {READ} LIMIT {rows}").df()
    preview_path = out_base.as_posix() + "_preview.csv"
    preview_df.to_csv(preview_path, index=False, encoding="utf-8")

    # Rowcount
    rowcount = int(con.sql(f"SELECT COUNT(*) FROM {READ}").fetchone()[0])
    return (str(src), rowcount, "OK", schema_path, profile_path, preview_path)

def main():
    ap = argparse.ArgumentParser(description="Validate all PSV files in a folder (or one file).")
    ap.add_argument("src", help="PSV file or folder")
    ap.add_argument("--pattern", default="*.psv", help="Glob when src is folder (default: *.psv)")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subfolders")
    ap.add_argument("--rows", type=int, default=100, help="Preview rows to save (default: 100)")
    args = ap.parse_args()

    src_path = Path(args.src).resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"Not found: {src_path}")

    # Build file list
    if src_path.is_file():
        files = [src_path]
    else:
        files = sorted(src_path.rglob(args.pattern) if args.recursive else src_path.glob(args.pattern))

    if not files:
        print("No files matched.")
        return

    with duckdb.connect() as con:
        results = []
        for f in files:
            print(f"-> {f}")
            res = validate_one(con, f, args.rows)
            results.append(res)
            print(f"   {res[2]}  rows={res[1]}")

    # Write rollup
    df = pd.DataFrame(results, columns=["file", "rows", "status", "schema", "profile", "preview"])
    summary = (src_path if src_path.is_dir() else src_path.parent) / "psv_validation_summary.csv"
    df.to_csv(summary, index=False, encoding="utf-8")

    print("\n=== SUMMARY ===")
    print(f"Total:   {len(df)}")
    print(f"OK:      {(df['status'] == 'OK').sum()}")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    main()
