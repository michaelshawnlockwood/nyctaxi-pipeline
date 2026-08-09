import ast
from pathlib import Path


source_path = Path("pydantic_model_validator_v1.1.py")
source_text = source_path.read_text(encoding="utf-8")
tree = ast.parse(source_text)

documented_items = []

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        docstring = ast.get_docstring(node)

        if docstring:
            documented_items.append((node.name, docstring))

for number, (name, docstring) in enumerate(documented_items, start=1):
    print(f"{number}. {name}: {docstring}")