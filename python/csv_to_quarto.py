from pathlib import Path
import pandas as pd
from typing import Any



PROFILE_CSV = Path("../data_out/yellow_tripdata_2026-05_profile.csv")
OUTPUT_QMD = Path("../data_out/yellow_tripdata_2026-05_profile.qmd")


def format_value(value: Any) -> str:
    """Format profile values for a reader-facing Markdown table."""
    if pd.isna(value):
        return "—"

    text = str(value)

    # Preserve timestamps and text values.
    try:
        number = float(text)
    except ValueError:
        return text

    # Format whole numbers with thousands separators.
    if number.is_integer():
        return f"{int(number):,}"

    # Avoid unnecessary trailing zeroes.
    return f"{number:,.10f}".rstrip("0").rstrip(".")


def build_profile_table(profile_csv: Path) -> tuple[str, pd.DataFrame]:
    raw = pd.read_csv(profile_csv, index_col=0)

    # The profile CSV contains one value column.
    values = raw.iloc[:, 0]

    row_count = format_value(values.get("__rowcount"))

    records: dict[str, dict[str, object]] = {}

    for key, value in values.items():
      key_text = str(key)

      if key_text == "__rowcount":
          continue

      column_name, separator, metric = key_text.rpartition("__")

      if not separator:
          continue

      records.setdefault(column_name, {})[metric] = value

    profile = (
        pd.DataFrame.from_dict(records, orient="index")
        .rename_axis("Column")
        .reset_index()
    )

    desired_columns = ["Column", "nulls", "example", "min", "max"]

    for column in desired_columns:
        if column not in profile.columns:
            profile[column] = pd.NA

    profile = profile[desired_columns].rename(
        columns={
            "nulls": "Nulls",
            "example": "Example",
            "min": "Minimum",
            "max": "Maximum",
        }
    )

    for column in ["Nulls", "Example", "Minimum", "Maximum"]:
        profile[column] = profile[column].map(format_value)

    profile["Column"] = profile["Column"].map(lambda value: f"`{value}`")

    return row_count, profile


def main() -> None:
    row_count, profile = build_profile_table(PROFILE_CSV)

    OUTPUT_QMD.parent.mkdir(parents=True, exist_ok=True)

    markdown = f"""\
## Complete Dataset Profile {{#sec-complete-dataset-profile}}

The dataset contains **{row_count} rows**.

{profile.to_markdown(index=False)}
"""

    OUTPUT_QMD.write_text(markdown, encoding="utf-8")

    print(f"Generated {OUTPUT_QMD}")


if __name__ == "__main__":
    main()