#!/usr/bin/env python3
"""
generate_sql_for_entity.py

Generate SQL Server CREATE TABLE DDL for entity/lookup tables
with PascalCase naming, plus seed data for PaymentType.
"""

import argparse
from pathlib import Path

# ---- Helpers ----

def pascal_case(name: str) -> str:
    """Convert snake_case or mixed names into PascalCase."""
    parts = name.replace("-", "_").split("_")
    return "".join(p.capitalize() for p in parts if p)

def render_entity(schema: str, table: str, cols: list[tuple[str,str,bool]], pk_cols=None) -> str:
    """Render CREATE TABLE DDL."""
    lines = []
    if pk_cols is None:
        pk_cols = []

    for colname, sqltype, nullable in cols:
        cname = f"[{pascal_case(colname)}]"
        nullness = "NULL" if nullable else "NOT NULL"
        lines.append(f"    {cname} {sqltype} {nullness}")

    pk_clause = ""
    if pk_cols:
        pk_clause = ",\n    CONSTRAINT [PK_{schema}_{table}] PRIMARY KEY CLUSTERED ({cols})".format(
            schema=schema,
            table=pascal_case(table),
            cols=", ".join(f"[{pascal_case(c)}]" for c in pk_cols)
        )

    ddl = (
        f"IF OBJECT_ID(N'[{schema}].[{pascal_case(table)}]', N'U') IS NOT NULL\n"
        f"    DROP TABLE [{schema}].[{pascal_case(table)}];\n"
        "GO\n\n"
        f"CREATE TABLE [{schema}].[{pascal_case(table)}] (\n"
        f"{',\n'.join(lines)}{pk_clause}\n"
        ");\n"
        "GO\n"
    )
    return ddl

def render_seed(schema: str, table: str, cols: list[str], rows: list[tuple]) -> str:
    """Render MERGE seed script."""
    col_list = ", ".join(f"[{pascal_case(c)}]" for c in cols)

    values_rows = ",\n  ".join(
        "(" + ", ".join(
            ("'" + val.replace("'", "''") + "'") if isinstance(val, str) else str(val) if val is not None else "NULL"
            for val in row
        ) + ")"
        for row in rows
    )

    merge = f"""
;WITH src({col_list}) AS (
  SELECT * FROM (VALUES
  {values_rows}
  ) v({col_list})
)
MERGE [{schema}].[{pascal_case(table)}] AS t
USING src AS s
  ON t.[{pascal_case(cols[0])}] = s.[{pascal_case(cols[0])}]
WHEN MATCHED AND t.[{pascal_case(cols[1])}] <> s.[{pascal_case(cols[1])}] THEN
  UPDATE SET {pascal_case(cols[1])} = s.[{pascal_case(cols[1])}]
WHEN NOT MATCHED BY TARGET THEN
  INSERT ({col_list}) VALUES ({", ".join("s." + c for c in col_list.split(", "))})
;
GO
"""
    return merge


# ---- Validate payment types ----
def validate_payment_types(parquet_path: str, expected_codes=(0,1,2,3,4,5,6)):
    import duckdb
    con = duckdb.connect()
    src = parquet_path.replace("\\", "/")
    q_summary = f"""
      WITH src AS (SELECT * FROM read_parquet('{src}'))
      SELECT CAST(payment_type AS INTEGER) AS payment_type,
             COUNT(*) AS trip_count
      FROM src
      GROUP BY 1
      ORDER BY 2 DESC
    """
    q_unexpected = f"""
      WITH src AS (SELECT * FROM read_parquet('{src}'))
      SELECT DISTINCT payment_type
      FROM src
      WHERE payment_type IS NULL
         OR CAST(payment_type AS INTEGER) NOT IN ({",".join(map(str,expected_codes))})
      ORDER BY 1
    """
    summary = con.sql(q_summary).df()
    unexpected = con.sql(q_unexpected).df()
    return summary, unexpected


# ---- Main ----
def main():
    ap = argparse.ArgumentParser(description="Generate SQL Server DDL + seed for PaymentType entity.")
    ap.add_argument("--schema", default="dbo", help="Target schema (default: dbo)")
    ap.add_argument("--out", default=None, help="Output folder (use: --out ./sql_out/sql_entities)")
    ap.add_argument("--effective-from", default="2025-03-18", help="EffectiveFrom default date")
    ap.add_argument("--parquet", help="Optional: path to a Parquet file to validate payment_type values against the TLC map.")
    args = ap.parse_args()

    if args.out is not None:
        out_dir = Path(args.out)
    else:
        # default to: <repo>/python/sql_out/sql_entities
        script_dir = Path(__file__).resolve().parent
        out_dir = script_dir / "sql_out" / "sql_entities"

    out_dir.mkdir(parents=True, exist_ok=True)

    if args.parquet:
        summary_df, unexpected_df = validate_payment_types(args.parquet)
    # write csvs next to the SQL for traceability
    (out_dir / "payment_type_summary.csv").write_text(summary_df.to_csv(index=False), encoding="utf-8")
    if len(unexpected_df) > 0:
        (out_dir / "payment_type_unexpected.csv").write_text(unexpected_df.to_csv(index=False), encoding="utf-8")
        print("WARNING: Unexpected payment_type values found. See payment_type_unexpected.csv")
    else:
        print("PaymentType validation: OK (no unexpected codes).")


    # ---- PaymentType entity definition ----
    table = "payment_type"
    cols = [
        ("payment_type_code","TINYINT",False),
        ("payment_type_name","VARCHAR(50)",False),
        ("effective_from","DATE",False),
        ("effective_to","DATE",True),
    ]
    pk_cols = ["payment_type_code"]

    # ---- PaymentType seed rows ----
    paymenttype_map = [
        (0, "Flex Fare trip", args.effective_from, None),
        (1, "Credit card",    args.effective_from, None),
        (2, "Cash",           args.effective_from, None),
        (3, "No charge",      args.effective_from, None),
        (4, "Dispute",        args.effective_from, None),
        (5, "Unknown",        args.effective_from, None),
        (6, "Voided trip",    args.effective_from, None),
    ]
    seed_cols = ["payment_type_code","payment_type_name","effective_from","effective_to"]

    # ---- Render ----
    ddl = render_entity(args.schema, table, cols, pk_cols)
    seed = render_seed(args.schema, table, seed_cols, paymenttype_map)

    # ---- Write ----
    ddl_path = out_dir / f"{args.schema}.{pascal_case(table)}.sql"
    seed_path = out_dir / f"{args.schema}.{pascal_case(table)}.seed.sql"
    (ddl_path).write_text(ddl, encoding="utf-8")
    (seed_path).write_text(seed, encoding="utf-8")

    print("Wrote:", ddl_path.name)
    print("Wrote:", seed_path.name)

if __name__ == "__main__":
    main()
