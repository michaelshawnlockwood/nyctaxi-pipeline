#!/usr/bin/env python3
"""
Generate SQL Server CREATE TABLE DDL from one or more data dictionary files.
"""

import argparse
from pathlib import Path
import csv, json
from collections import defaultdict

# ---------- Helpers ----------

def try_float(x):
    try:
        return float(x)
    except Exception:
        return None

def choose_int_width(min_val, max_val):
    if min_val is None or max_val is None:
        return "INT"
    nonneg = (min_val >= 0)
    if nonneg and 0 <= max_val <= 255:
        return "TINYINT"
    if -32768 <= min_val <= 32767 and -32768 <= max_val <= 32767:
        return "SMALLINT"
    if -2147483648 <= min_val <= 2147483647 and -2147483648 <= max_val <= 2147483647:
        return "INT"
    return "BIGINT"

def map_sql_type(row, char_mode="VARCHAR"):
    t = str(row.get("type",""))
    t = t.strip().upper()
    if t == "TIMESTAMP":
        return "DATETIME2"
    if t == "BIGINT":
        mn = try_float(row.get("min"))
        mx = try_float(row.get("max"))
        return choose_int_width(mn, mx)
    if t == "DOUBLE":
        return "DECIMAL(18,4)"
    if t in ("VARCHAR","STRING","NVARCHAR","CHAR","NCHAR"):
        # size heuristic from example
        ex = row.get("example")
        if isinstance(ex, str) and len(ex) > 0:
            ln = max(1, min(len(ex), 100))
        else:
            ln = 10
        base = char_mode if t in ("VARCHAR","STRING") else t  # honor explicit NVARCHAR/CHAR/NCHAR
        return f"{base}({ln})"
    # pass-through (e.g., INT, DECIMAL(10,2) if already in dictionary)
    return t

def is_nullable(row):
    n = try_float(row.get("nulls"))
    if n is None:
        return True
    return n > 0

TRUE_SET = {"y","yes","true","1","t"}
def yes(val):
    if val is None:
        return False
    return str(val).strip().lower() in TRUE_SET

def render_table(schema, table, rows, char_mode="VARCHAR"):
    lines = []
    pk_cols = []  # optional future extension

    for r in rows:
        colname = f"[{r['column']}]"
        sql_type = map_sql_type(r, char_mode=char_mode)
        nullness = "NULL" if is_nullable(r) else "NOT NULL"

        identity_clause = ""
        if yes(r.get("identity")):
            def _ival(v, d=1):
                if v in (None, "", "nan"):
                    return d
                try:
                    return int(str(v).strip())
                except Exception:
                    return d
            seed = _ival(r.get("identity_seed"), 1)
            incr = _ival(r.get("identity_increment"), 1)
            identity_clause = f" IDENTITY({seed},{incr})"

        default_val = r.get("default")
        default_clause = f" DEFAULT ({default_val})" if default_val not in (None, "", "nan") else ""

        lines.append(f"    {colname} {sql_type}{identity_clause}{default_clause} {nullness}")
        if yes(r.get("pk")):
            pk_cols.append(colname)

    pk_clause = ""
    if pk_cols:
        pk_clause = ",\n    CONSTRAINT [PK_{0}_{1}] PRIMARY KEY CLUSTERED ({2})".format(
            schema, table, ", ".join(pk_cols)
        )

    ddl = (
        "IF OBJECT_ID(N'[{schema}].[{table}]', N'U') IS NOT NULL\n"
        "    DROP TABLE [{schema}].[{table}];\n"
        "GO\n\n"
        "CREATE TABLE [{schema}].[{table}] (\n"
        "{columns}{pk}\n"
        ");\n"
        "GO\n"
    ).format(schema=schema, table=table, columns=",\n".join(lines), pk=pk_clause)
    return ddl

def load_csv(path: Path):
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # normalize expected keys, but keep flexible naming
            row = {k.lower(): v for k,v in r.items()}
            # Map common header variants into canonical keys
            norm = {
                "column": row.get("column") or row.get("column_name") or row.get("name"),
                "type": row.get("type") or row.get("data_type"),
                "nulls": row.get("nulls") or row.get("is_nullable"),
                "example": row.get("example"),
                "min": row.get("min"),
                "max": row.get("max"),
                "identity": row.get("identity") or row.get("is_identity"),
                "identity_seed": row.get("identity_seed") or row.get("identity_start"),
                "identity_increment": row.get("identity_increment") or row.get("identity_incr"),
                "default": row.get("default") or row.get("column_default"),
                "pk": row.get("pk") or row.get("is_pk") or row.get("primary_key"),
            }
            rows.append(norm)
    return rows

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for r in data:
        row = {k.lower(): v for k,v in r.items()}
        norm = {
            "column": row.get("column") or row.get("column_name") or row.get("name"),
            "type": row.get("type") or row.get("data_type"),
            "nulls": row.get("nulls") or row.get("is_nullable"),
            "example": row.get("example"),
            "min": row.get("min"),
            "max": row.get("max"),
            "identity": row.get("identity") or row.get("is_identity"),
            "identity_seed": row.get("identity_seed") or row.get("identity_start"),
            "identity_increment": row.get("identity_increment") or row.get("identity_incr"),
            "default": row.get("default") or row.get("column_default"),
            "pk": row.get("pk") or row.get("is_pk") or row.get("primary_key"),
        }
        rows.append(norm)
    return rows

def build_parser():
    desc = """
Generate SQL Server CREATE TABLE DDL from one or more data dictionary files.

Dictionary formats supported
----------------------------
- CSV (*.dictionary.csv): headers should include at least 'column', 'type', 'nulls'.
  Optional headers: 'example', 'min', 'max', 'identity', 'identity_seed',
                    'identity_increment', 'default', 'pk'.
- JSON (*.dictionary.json): list of objects with the same keys as above.

Type mapping rules
------------------
- TIMESTAMP    -> DATETIME2
- BIGINT       -> down-sized to TINYINT/SMALLINT/INT/BIGINT based on min/max
- DOUBLE       -> DECIMAL(18,4)
- VARCHAR/STRING -> {VARCHAR|NVARCHAR}(N)  (N inferred from 'example' length, capped at 100; default 10)
- Other types pass through unchanged (e.g., INT, DECIMAL(10,2), DATE, TIME, etc.)

Nullability
-----------
- If 'nulls' > 0, column is created as NULL, otherwise NOT NULL.

IDENTITY
--------
- If 'identity' is truthy (Y/Yes/True/1), an IDENTITY(seed,increment) is emitted.
- Defaults: seed=1, increment=1 if not provided (identity_seed/identity_increment).

Primary Key
-----------
- If 'pk' is truthy, the column is included in a clustered PRIMARY KEY constraint.
- Composite keys are supported: mark 'pk' on multiple columns.

String Type Mode
----------------
- Use --char to choose VARCHAR (default) or NVARCHAR for generic string columns
  ('VARCHAR'/'STRING' in the dictionary). Explicit 'NVARCHAR', 'CHAR', 'NCHAR'
  in the dictionary are honored as-is and not overridden.

Outputs
-------
- One <schema>.<table>.sql per table
- create_all.sql aggregating all generated tables in the output folder
"""
    epilog = """
Examples
--------
# 1) Generate from a folder of Phase-2 dictionaries (*.dictionary.csv)
python generate_sql_from_dictionary.py ./phase2_dicts --schema staging --out ./sql_out

# 2) Generate from one CSV and one JSON file, emit NVARCHAR for generic strings
python generate_sql_from_dictionary.py yellow.dictionary.csv other.dictionary.json --char NVARCHAR --out ./sql_out

# 3) Mix files and folders; default VARCHAR for strings
python generate_sql_from_dictionary.py ./dicts ./one.dictionary.csv --schema dbo --out ./sql

Notes
-----
- You can pass multiple files and/or folders. Folders are searched for *.dictionary.csv.
- Table name is derived from the filename (e.g., 'yellow_tripdata.dictionary.csv' -> 'yellow_tripdata').
- If a dictionary provides explicit types like DECIMAL(12,2), they pass through unchanged.
- This tool only emits DDL; apply it with sqlcmd/SSMS as appropriate.
"""
    return argparse.ArgumentParser(
        description=desc,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

def main():
    ap = build_parser()
    ap.add_argument("input", nargs="+", help="One or more files or folders. Folders will search for *.dictionary.csv")
    ap.add_argument("--schema", default="dbo", help="Target schema name (default: dbo)")
    ap.add_argument("--out", default="sql_out", help="Output folder for .sql files (default: ./sql_out)")
    ap.add_argument("--char", dest="char_mode", choices=["VARCHAR","NVARCHAR"], default="VARCHAR",
                    help="String type to emit for generic string columns (default: VARCHAR)")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect (table_name -> rows)
    tables = defaultdict(list)

    for inp in args.input:
        p = Path(inp)
        if p.is_dir():
            for f in sorted(p.glob("*.dictionary.csv")):
                table = f.name.replace(".dictionary.csv","")
                rows = load_csv(f)
                tables[(args.schema, table)] = rows
        else:
            if p.suffix.lower() == ".csv":
                table = p.stem.replace(".dictionary","")
                rows = load_csv(p)
                tables[(args.schema, table)] = rows
            elif p.suffix.lower() == ".json":
                table = p.stem.replace(".dictionary","")
                rows = load_json(p)
                tables[(args.schema, table)] = rows
            else:
                print(f"Skipping unsupported input: {p}")

    aggregate = []
    for (schema, table), rows in tables.items():
        if not rows:
            continue
        ddl = render_table(schema, table, rows, char_mode=args.char_mode)
        (out_dir / f"{schema}.{table}.sql").write_text(ddl, encoding="utf-8")
        aggregate.append(ddl)

    (out_dir / "create_all.sql").write_text("".join(aggregate), encoding="utf-8")
    print(f"Generated {len(aggregate)} table script(s) in {out_dir.resolve()}")
    for f in sorted(out_dir.glob("*.sql")):
        print(" -", f.name)

if __name__ == "__main__":
    main()
