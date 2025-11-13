#!/usr/bin/env python3
"""
read_entities.py
Read entity definition JSON files and extract:
  - entity (name)
  - header (first row of labels)
  - rows (subsequent rows)
  - source.file (optional)
  - source.column (optional)

Search path: <repo>/data_in/entities/*.json
"""

import json
from pathlib import Path
from typing import Iterator, TypedDict, List, Any, Optional

class EntitySpec(TypedDict, total=False):
    entity: str
    header: List[str]
    rows: List[List[Any]]
    source_file: Optional[str]
    source_column: Optional[str]
    raw_path: str

def iter_entities(entities_dir: Path) -> Iterator[EntitySpec]:
    for jf in sorted(entities_dir.glob("*.json")):
        spec = json.loads(jf.read_text(encoding="utf-8"))
        labels = spec.get("labels") or []
        if not labels or len(labels) < 1:
            # Emit skeleton for visibility; skip if you prefer strictness
            yield EntitySpec(
                entity=spec.get("entity", jf.stem),
                header=[],
                rows=[],
                source_file=(spec.get("source") or {}).get("file"),
                source_column=(spec.get("source") or {}).get("column"),
                raw_path=str(jf),
            )
            continue

        header = labels[0]
        rows = labels[1:] if len(labels) > 1 else []

        yield EntitySpec(
            entity=spec.get("entity", jf.stem),
            header=header,
            rows=rows,
            source_file=(spec.get("source") or {}).get("file"),
            source_column=(spec.get("source") or {}).get("column"),
            raw_path=str(jf),
        )

def main():
    # repo-relative: script expected in <repo>/python/
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    entities_dir = repo_root / "data_in" / "entities"

    if not entities_dir.exists():
        print(f"Entities folder not found: {entities_dir}")
        return

    for e in iter_entities(entities_dir):
        print(f"\n=== {e['entity']} ===")
        print(f"file: {e.get('source_file')}")
        print(f"column: {e.get('source_column')}")
        print(f"json: {e['raw_path']}")
        print(f"header: {e.get('header')}")
        if e.get("rows"):
            print(f"rows[0..2]: {e['rows'][:3]}  (total={len(e['rows'])})")
        else:
            print("rows: []")

if __name__ == "__main__":
    main()
