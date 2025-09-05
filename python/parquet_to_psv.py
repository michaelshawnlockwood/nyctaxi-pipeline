# parquet_to_psv.py
import argparse
from pathlib import Path
import duckdb
import pandas as pd

def to_posix(p: Path) -> str:
    return str(p).replace("\\", "/")

def convert_one(con,
                src: Path,
                out_root: Path,
                base_root: Path,
                flat: bool,
                overwrite: bool,
                limit: int | None):
    """
    Returns: (file, source_rows, written_rows, limit, status, out_path)
    """
    src = src.resolve()
    if not src.exists():
        return (str(src), None, None, limit, "NOT_FOUND", None)

    # Build output path: mirror from base_root unless --flat
    rel = Path(src.name) if flat else src.relative_to(base_root)
    out_path = (out_root / rel).with_suffix(".psv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    SRC = to_posix(src)

    # Compute source rowcount up front (cheap in DuckDB)
    source_rows = int(con.sql(f"SELECT COUNT(*) FROM read_parquet('{SRC}')").fetchone()[0])

    if out_path.exists() and not overwrite:
        # We didn't write the file, but for summary we still show written_rows as the file's current rows
        # Try to read the PSV quickly to report its size; if it fails, leave as None.
        written_rows = None
        try:
            written_rows = int(con.sql(
                f"SELECT COUNT(*) FROM read_csv('{to_posix(out_path)}', delim='|', header=True, quote='\"', escape='\"')"
            ).fetchone()[0])
        except Exception:
            pass
        return (str(src), source_rows, written_rows, limit, "SKIPPED_EXISTS", str(out_path))

    # Prepare SELECT with optional LIMIT for writing
    base_sql = f"SELECT * FROM read_parquet('{SRC}')"
    limited = False
    if limit is not None:
        base_sql += f" LIMIT {limit}"
        limited = True

    # Write PSV
    copy_sql = f"""
        COPY ({base_sql})
        TO '{to_posix(out_path)}'
        WITH (
            HEADER,
            DELIMITER '|',
            QUOTE '"',
            ESCAPE '"',
            NULL '',
            DATEFORMAT '%Y-%m-%d',
            TIMESTAMPFORMAT '%Y-%m-%d %H:%M:%S'
        );
    """
    con.sql(copy_sql)

    # Determine rows actually written
    if limit is None:
        written_rows = source_rows
    else:
        written_rows = min(source_rows, limit)

    # Status logic
    if limited and written_rows < source_rows:
        status = "LIMITED"
    else:
        status = "OK"

    return (str(src), source_rows, written_rows, limit, status, str(out_path))

def main():
    ap = argparse.ArgumentParser(
        description="Convert Parquet files to PSV (pipe-separated) using DuckDB."
    )
    ap.add_argument("src", help="Path to a Parquet file OR a folder containing Parquet files")
    ap.add_argument("--pattern", default="*.parquet", help="Glob when src is a folder (default: *.parquet)")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subfolders")
    ap.add_argument("--out-dir", default="data_out", help="Output root directory (default: data_out)")
    ap.add_argument("--flat", action="store_true", help="Do not mirror folder structure under out-dir")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing .psv files")
    ap.add_argument("--limit", type=int, default=None, help="Limit rows per file (testing). Marked as LIMITED in summary if < source_rows.")
    ap.add_argument("--dry-run", action="store_true", help="List what would be converted, then exit")
    args = ap.parse_args()

    src_path = Path(args.src).resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"Not found: {src_path}")

    out_root = Path(args.out_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    # Build file list + base_root for mirroring
    if src_path.is_file():
        files = [src_path]
        base_root = src_path.parent
    else:
        files = sorted(src_path.rglob(args.pattern) if args.recursive else src_path.glob(args.pattern))
        base_root = src_path

    if not files:
        print("No files matched.")
        return

    print(f"Converting {len(files)} file(s) → {out_root}")

    if args.dry_run:
        for f in files:
            rel = Path(f.name) if args.flat else f.relative_to(base_root)
            out_path = (out_root / rel).with_suffix(".psv")
            print(f"DRY-RUN  {f}  ->  {out_path}")
        return

    results = []
    with duckdb.connect() as con:
        for f in files:
            print(f"-> {f}")
            file_str, source_rows, written_rows, limit, status, outp = convert_one(
                con=con,
                src=f,
                out_root=out_root,
                base_root=base_root,
                flat=args.flat,
                overwrite=args.overwrite,
                limit=args.limit
            )
            results.append((file_str, source_rows, written_rows, limit, status, outp))
            if status == "LIMITED":
                print(f"   ⚠️  LIMITED: wrote {written_rows:,} of {source_rows:,} rows (limit={limit})  out={outp}")
            else:
                print(f"   {status}  rows={written_rows:,}  out={outp}")

    # Rollup CSV in out_dir
    df = pd.DataFrame(results, columns=["file", "source_rows", "written_rows", "limit", "status", "out"])
    rollup = out_root / "psv_conversion_summary.csv"
    df.to_csv(rollup, index=False, encoding="utf-8")

    print("\n=== SUMMARY ===")
    print(f"Total:    {len(df)}")
    print(f"OK:       {(df['status'] == 'OK').sum()}")
    print(f"LIMITED:  {(df['status'] == 'LIMITED').sum()}")
    print(f"Skipped:  {(df['status'] == 'SKIPPED_EXISTS').sum()}")
    print(f"Summary:  {rollup}")

if __name__ == "__main__":
    main()
