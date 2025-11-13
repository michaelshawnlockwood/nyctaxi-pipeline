#!/usr/bin/env python3
"""
build_entity_ddl.py

Usage:
  python build_entity_ddl.py --entity-json ../data_in/entities/PaymentType.json
  python build_entity_ddl.py --entities-dir ../data_in/entities

Writes: <repo>/python/sql_out/sql_entities/dbo.<Entity>.sql
DDL only (no seeding).
"""

import argparse, json
from pathlib import Path
from typing import List, Any

# ---- type inference helpers ----

def choose_int_width(values: List[int]) -> str:
    if not values: return "INT"
    mn, mx = min(values), max(values)
    if 0 <= mn and mx <= 255: return "TINYINT"
    if -32768 <= mn and mx <= 32767: return "SMALLINT"
    if -2147483648 <= mn and mx <= 2147483647: return "INT"
    return "BIGINT"

def choose_varchar_width(values: List[str], pad=0, cap=4000) -> str:
    if not values: return "VARCHAR(100)"
    width = min(max((max(len(s or "") for s in values) + pad), 1), cap)
    return f"VARCHAR({width})"

def bracket(name: str) -> str:
    return f"[{name}]"

# ---- core function ----

def build_entity_ddl(entity_path: Path, out_dir: Path, schema="dbo"):
    spec = json.loads(entity_path.read_text(encoding="utf-8"))
    entity = spec.get("entity", entity_path.stem)

    labels = spec.get("labels") or []
    if len(labels) < 1:
        raise ValueError(f"{entity_path}: labels must contain at least a header row")

    header = labels[0]
    rows   = labels[1:]
    if len(header) < 2:
        raise ValueError(f"{entity_path}: header must have ≥2 cols (ID, Name)")

    id_col, name_col = header[0], header[1]

    # Collect samples for inference
    id_vals, name_vals = [], []
    for r in rows:
        if len(r) >= 1 and r[0] is not None:
            try: id_vals.append(int(r[0]))
            except: pass
        if len(r) >= 2 and r[1] is not None:
            name_vals.append(str(r[1]))

    id_sql   = choose_int_width(id_vals or [0])
    name_sql = choose_varchar_width(name_vals)

    cols = [
        f"    {bracket(id_col)} {id_sql} NOT NULL",
        f"    {bracket(name_col)} {name_sql} NOT NULL",
        f"    [EffectiveFrom] DATE NOT NULL",
        f"    [EffectiveTo]   DATE NULL",
        f"    CONSTRAINT [PK_{schema}_{entity}] PRIMARY KEY CLUSTERED ({bracket(id_col)})"
    ]

    ddl = (
        f"IF OBJECT_ID(N'[{schema}].[{entity}]', N'U') IS NOT NULL\n"
        f"    DROP TABLE [{schema}].[{entity}];\n"
        "GO\n\n"
        f"CREATE TABLE [{schema}].[{entity}] (\n"
        + ",\n".join(cols) +
        "\n);\nGO\n"
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{schema}.{entity}.sql"
    out_path.write_text(ddl, encoding="utf-8")
    print(f"Wrote: {out_path}")

# ---- CLI ----

def main():
    ap = argparse.ArgumentParser(description="Generate DDL from entity definition JSON(s).")
    ap.add_argument("--entity-json", nargs="*", help="Path(s) to individual entity JSON files")
    ap.add_argument("--entities-dir", help="Directory containing *.json entity files")
    ap.add_argument("--schema", default="dbo")
    ap.add_argument("--out", default=None, help="Output folder (default: ./python/sql_out/sql_entities)")
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    default_out = script_dir / "sql_out" / "sql_entities"
    out_dir = Path(args.out) if args.out else default_out

    files = []
    if args.entity_json: files.extend(Path(f) for f in args.entity_json)
    if args.entities_dir: files.extend(sorted(Path(args.entities_dir).glob("*.json")))
    if not files:
        ap.error("Specify --entity-json <file(s)> or --entities-dir <dir>")

    for f in files:
        build_entity_ddl(f, out_dir, schema=args.schema)

if __name__ == "__main__":
    main()
