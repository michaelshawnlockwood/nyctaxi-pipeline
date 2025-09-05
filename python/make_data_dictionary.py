# make_data_dictionary.py
import argparse
from pathlib import Path
import duckdb
import pandas as pd

def to_posix(p: Path) -> str:
    return str(p).replace("\\", "/")

def getv(df: pd.DataFrame, key: str):
    try:
        return df.loc[key, "value"]
    except Exception:
        return None

def build_dictionary(psv_path: Path, out_override: Path | None):
    p = psv_path.resolve()
    SRC = to_posix(p)
    con = duckdb.connect()

    READ = f"read_csv('{SRC}', delim='|', header=True, quote='\"', escape='\"')"

    # Schema
    schema_df = con.sql(f"DESCRIBE SELECT * FROM {READ}").df()

    # Profile
    exprs = []
    for _, r in schema_df.iterrows():
        col = r["column_name"]
        typ = str(r["column_type"]).upper()
        exprs.append(f"SUM((\"{col}\" IS NULL) OR CAST(\"{col}\" AS VARCHAR)='') AS \"{col}__nulls\"")
        exprs.append(f"MIN(NULLIF(CAST(\"{col}\" AS VARCHAR), '')) AS \"{col}__example\"")
        if any(k in typ for k in ["INT", "REAL", "DECIMAL", "DOUBLE", "FLOAT", "DATE", "TIME", "TIMESTAMP"]):
            exprs.append(f"MIN(\"{col}\") AS \"{col}__min\"")
            exprs.append(f"MAX(\"{col}\") AS \"{col}__max\"")

    profile_sql = f"WITH src AS (SELECT * FROM {READ}) SELECT {', '.join(exprs)} FROM src"
    prof = con.sql(profile_sql).df().T
    prof.columns = ["value"]

    # Assemble dictionary
    rows = []
    for _, r in schema_df.iterrows():
        col = r["column_name"]
        typ = r["column_type"]
        rows.append([col, typ,
                     getv(prof, f"{col}__nulls"),
                     getv(prof, f"{col}__example"),
                     getv(prof, f"{col}__min"),
                     getv(prof, f"{col}__max")])
    dd_df = pd.DataFrame(rows, columns=["column", "type", "nulls", "example", "min", "max"])

    # Output base: drop month → yellow_tripdata.dictionary.*
    if out_override:
        out_base = out_override
    else:
        out_base = p.parent / "yellow_tripdata.dictionary"

    out_csv = out_base.with_suffix(".csv")
    dd_df.to_csv(out_csv, index=False, encoding="utf-8")

    try:
        import tabulate  # noqa: F401
        out_md = out_base.with_suffix(".md")
        dd_df.to_markdown(out_md, index=False)
        print(f"Data dictionary written:\n- {out_csv}\n- {out_md}")
    except ImportError:
        print(f"Data dictionary written (CSV only):\n- {out_csv}\n⚠️ Install 'tabulate' to also generate Markdown.")

def main():
    ap = argparse.ArgumentParser(description="Generate one unified data dictionary from PSV file(s).")
    ap.add_argument("src", help="Path to a PSV file OR folder containing PSV files")
    ap.add_argument("--pattern", default="*.psv", help="Glob when src is folder (default: *.psv)")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subfolders when src is a folder")
    ap.add_argument("--out", help="Override output file base (omit extension)")
    args = ap.parse_args()

    src_path = Path(args.src).resolve()
    if not src_path.exists():
        raise FileNotFoundError(src_path)

    # Resolve file to use
    if src_path.is_file():
        psv_file = src_path
    else:
        files = sorted(src_path.rglob(args.pattern) if args.recursive else src_path.glob(args.pattern))
        if not files:
            print("No PSV files found.")
            return
        psv_file = files[0]   # just take the first one

    out_override = Path(args.out).resolve() if args.out else None
    print(f"Building unified data dictionary from: {psv_file}")
    build_dictionary(psv_file, out_override)

if __name__ == "__main__":
    main()
