# merge_parquet.py
import argparse
from pathlib import Path
import duckdb

def to_posix(p: Path) -> str:
    return str(p).replace("\\", "/")

def main():
    ap = argparse.ArgumentParser(description="Merge many Parquet files into one Parquet file (single output).")
    ap.add_argument("src", help="Folder or a single Parquet file")
    ap.add_argument("--pattern", default="*.parquet", help="Glob when src is a folder (default: *.parquet)")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subfolders")
    ap.add_argument("--out", required=True, help="Output Parquet path, e.g., ../data_out/_temp/merged.parquet")
    ap.add_argument("--compression", default="ZSTD", help="Parquet compression (ZSTD,SNAPPY,GZIP; default ZSTD)")
    args = ap.parse_args()

    src_path = Path(args.src).resolve()
    if not src_path.exists():
        raise FileNotFoundError(src_path)

    # Build file list
    if src_path.is_file():
        files = [src_path]
    else:
        it = src_path.rglob(args.pattern) if args.recursive else src_path.glob(args.pattern)
        files = sorted(it)

    if not files:
        raise SystemExit("No Parquet files matched.")

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use DuckDB to read and write a single Parquet
    with duckdb.connect() as con:
        # DuckDB can take a list of files directly in read_parquet([...])
        file_list_sql = "[" + ",".join(f"'{to_posix(f)}'" for f in files) + "]"
        con.sql(f"""
            COPY (
                SELECT * FROM read_parquet({file_list_sql})
            )
            TO '{to_posix(out_path)}'
            (FORMAT 'PARQUET', COMPRESSION '{args.compression}');
        """)

    print(f"Merged {len(files)} file(s) → {out_path}")

if __name__ == "__main__":
    main()
