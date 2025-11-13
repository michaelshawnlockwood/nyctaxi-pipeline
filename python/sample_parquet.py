# sample_parquet.py
# Purpose: For each monthly NYC Taxi Parquet file, write a reduced Parquet that
#          keeps ~ --sample (e.g., 0.05) of rows per *day* using Bernoulli sampling,
#          with deterministic randomness via PRAGMA random_seed.
#
# Example:
#   python sample_parquet.py "D:/nyctaxi/data_in" --recursive --sample .05 \
#       --out-root "../data_out/reduced" --date-column tpep_pickup_datetime --seed 42
#
# Output naming:
#   If input looks like: yellow_tripdata_2025-01.parquet
#   Output becomes:      yellow_tripdata_reduced_2025-01.parquet
#   Otherwise we append: <stem>_reduced_<YYYY-MM>.parquet
#
# Notes:
#   - Preserves original columns/types (no casts). We only add temp columns for processing and exclude them on write.
#   - Excludes rows where the date-column is NULL. (Adjust if needed.)
#   - Logs per-day totals and sampled counts for quick sanity checks.
#   - Overwrite is off by default; use --force to overwrite existing outputs.

import argparse
from pathlib import Path
import re
import sys
import duckdb

def to_posix(p: Path) -> str:
    return str(p).replace("\\", "/")

def derive_output_name(infile: Path) -> str:
    stem = infile.stem  # e.g., 'yellow_tripdata_2025-01'
    m = re.search(r'_(\d{4}-\d{2})(?:$|_)', stem)
    if m:
        new_stem = stem[:m.start()] + "_reduced" + stem[m.start():]
    else:
        # Fallback: just append if no YYYY-MM pattern is found
        new_stem = stem + "_reduced"
    return new_stem + infile.suffix

def resolve_inputs(src: Path, pattern: str, recursive: bool):
    if src.is_file():
        return [src]
    it = src.rglob(pattern) if recursive else src.glob(pattern)
    files = sorted(p for p in it if p.is_file())
    return files

def main():
    ap = argparse.ArgumentParser(
        description="Sample each Parquet file by ~N% per day and write a reduced Parquet per input file."
    )
    ap.add_argument("src", help="Folder or a single Parquet file")
    ap.add_argument("--pattern", default="*.parquet", help="Glob when src is a folder (default: *.parquet)")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subfolders")
    ap.add_argument("--out-root", default="../data_out/reduced", help="Output folder root (default: ../data_out/reduced)")
    ap.add_argument("--date-column", default="tpep_pickup_datetime", help="Timestamp column used for day grouping")
    ap.add_argument("--sample", type=float, default=0.05, help="Bernoulli sampling rate (e.g., 0.05 or .05)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for determinism (DuckDB PRAGMA random_seed)")
    ap.add_argument("--compression", default="ZSTD", help="Parquet compression (ZSTD,SNAPPY,GZIP; default ZSTD)")
    ap.add_argument("--force", action="store_true", help="Overwrite output files if they already exist")
    args = ap.parse_args()

    src_path = Path(args.src).resolve()
    if not src_path.exists():
        raise FileNotFoundError(src_path)

    files = resolve_inputs(src_path, args.pattern, args.recursive)
    if not files:
        print("No Parquet files matched.", file=sys.stderr)
        sys.exit(2)

    out_root = Path(args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if not (0.0 < args.sample < 1.0):
        print("--sample must be in (0, 1).", file=sys.stderr)
        sys.exit(2)

    print(f"Sampling {args.sample*100:.2f}% of rows per day | date-column: {args.date_column} | seed={args.seed}")
    print(f"Writing outputs under: {out_root}")
    print(f"Compression: {args.compression}")
    print("-----------------------------------------------------")

    # One DuckDB connection reused across files for efficiency.
    with duckdb.connect() as con:
        con.execute("SET threads=1")
        con.execute(f"SELECT setseed({args.seed % 1});")

        for idx, infile in enumerate(files, 1):
            in_posix = to_posix(infile.resolve())
            print(f"[{idx}/{len(files)}] Processing: {infile}")

            # Validate that the date column exists and derive month boundaries from data
            try:
                con.execute(f"""
                    CREATE OR REPLACE TEMP VIEW _v AS
                    SELECT * FROM read_parquet('{in_posix}');
                """)
                # Ensure date column exists
                info = con.execute("PRAGMA table_info('_v')").fetchall()
                cols = [row[1] for row in info]  # index 1 = column name
                colset = {c.lower() for c in cols}

                if args.date_column.lower() not in colset:
                    print(f"  ! Skipping: column '{args.date_column}' not found.", file=sys.stderr)
                    print(f"    Available columns: {', '.join(cols)}")  # (optional, helps debug)
                    con.execute("DROP VIEW _v;")
                    continue

                # Derive month from data
                month_info = con.execute(f"""
                    SELECT
                        strftime('%Y-%m', min(date_trunc('month', {args.date_column}))) AS min_month,
                        strftime('%Y-%m', max(date_trunc('month', {args.date_column}))) AS max_month,
                        COUNT(DISTINCT strftime('%Y-%m', date_trunc('month', {args.date_column}))) AS distinct_months
                    FROM _v
                    WHERE {args.date_column} IS NOT NULL;
                """).fetchone()

                if month_info is None or month_info[0] is None:
                    print("  ! No non-null dates; skipping.", file=sys.stderr)
                    con.execute("DROP VIEW _v;")
                    continue

                min_month, max_month, distinct_months = month_info
                if distinct_months != 1:
                    print(f"  ! Warning: data spans multiple months ({min_month}..{max_month}); "
                          f"naming will use min month.", file=sys.stderr)
                month_yyyy_mm = min_month

                # Precompute rnd and pickup_day once to allow logging + write
                con.execute(f"""
                    CREATE OR REPLACE TEMP TABLE _pre AS
                    SELECT
                        *,
                        date_trunc('day', {args.date_column}) AS pickup_day,
                        random() AS _rnd
                    FROM _v
                    WHERE {args.date_column} IS NOT NULL;
                """)

                # Quick stats per day (total & sampled expectation)
                # We'll compute the *actual* sampled counts using the same predicate.
                day_stats = con.execute(f"""
                    SELECT
                        pickup_day::DATE AS day,
                        COUNT(*) AS total_rows,
                        SUM((_rnd < {args.sample})::INT) AS sampled_rows
                    FROM _pre
                    GROUP BY 1
                    ORDER BY 1;
                """).fetchall()

                # Construct output path
                out_name = derive_output_name(infile)
                out_path = out_root / out_name
                if out_path.exists() and not args.force:
                    print(f"  ! Output exists, skipping (use --force to overwrite): {out_path}", file=sys.stderr)
                    con.execute("DROP TABLE _pre; DROP VIEW _v;")
                    continue

                # Write sampled rows, excluding temp columns
                con.execute(f"""
                    COPY (
                        SELECT * EXCLUDE (pickup_day, _rnd)
                        FROM _pre
                        WHERE _rnd < {args.sample}
                    )
                    TO '{to_posix(out_path)}'
                    (FORMAT 'PARQUET', COMPRESSION '{args.compression}');
                """)

                # Summaries
                total_in = con.execute("SELECT COUNT(*) FROM _pre;").fetchone()[0]
                total_out = con.execute(f"SELECT COUNT(*) FROM _pre WHERE _rnd < {args.sample};").fetchone()[0]
                con.execute("DROP TABLE _pre; DROP VIEW _v;")

                print(f"  ✓ Wrote: {out_path}")
                print(f"    Rows in:  {total_in:,}")
                print(f"    Rows out: {total_out:,}  (~{(total_out/max(total_in,1))*100:.2f}%)")
                # Print a compact per-day summary (first/last 3 to avoid spam)
                if day_stats:
                    preview = day_stats[:3] + ([("...", None, None)] if len(day_stats) > 6 else []) + day_stats[-3:] if len(day_stats) > 6 else day_stats
                    print("    Per-day (day | total → sampled):")
                    for d, t, s in preview:
                        if d == "...":
                            print("      ...")
                        else:
                            print(f"      {d} | {t:,} → {s:,}")

            except Exception as ex:
                print(f"  ! Error on {infile}: {ex}", file=sys.stderr)
                try:
                    con.execute("DROP TABLE IF EXISTS _pre; DROP VIEW IF EXISTS _v;")
                except Exception:
                    pass
                continue

    print("Done.")

if __name__ == "__main__":
    main()
