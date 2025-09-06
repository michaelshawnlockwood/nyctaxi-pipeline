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

    # ---- Output naming (fixed) ----
    if out_override:
        # If user passed a directory, write <stem>.dictionary.* there.
        if out_override.is_dir():
            out_base = out_override / f"{p.stem}.dictionary"
        else:
            # Treat as a full base path (no extension expected)
            out_base = out_override
    else:
        # Default: next to the input file, using its stem
        out_base = p.with_suffix("")  # D:\...\mpccpepd
        out_base = out_base.parent / f"{out_base.name}_dictionary"  # ...\mpccpepd.dictionary

    out_csv = out_base.with_suffix(".csv")
    dd_df.to_csv(out_csv, index=False, encoding="utf-8")

    try:
        import tabulate  # noqa: F401
        out_md = out_base.with_suffix(".md")
        dd_df.to_markdown(out_md, index=False)
        print(f"Data dictionary written:\n- {out_csv}\n- {out_md}")
    except ImportError:
        print(f"Data dictionary written (CSV only):\n- {out_csv}\nInstall 'tabulate' to also generate Markdown.")

def main():
    ap = argparse.ArgumentParser(description="Generate a unified data dictionary from a PSV file.")
    ap.add_argument("src", help="Path to a PSV file")
    ap.add_argument("--out", help="Output base path or directory (omit extension). "
                                  "Default: <src-stem>.dictionary next to the input file.")
    args = ap.parse_args()

    psv_file = Path(args.src).resolve()
    if not psv_file.exists() or not psv_file.is_file():
        raise FileNotFoundError(psv_file)

    out_override = Path(args.out).resolve() if args.out else None
    print(f"Building unified data dictionary from: {psv_file}")
    build_dictionary(psv_file, out_override)

if __name__ == "__main__":
    main()
