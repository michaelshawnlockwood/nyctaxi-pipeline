from pathlib import Path
import streamlit as st
from datetime import datetime
import pyarrow.parquet as pq
import tomllib
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SCRIPT_DIR / "validator" / "config.toml"

def load_config(config_path: Path) -> dict[str, Any]:
    """Load validator configuration from a TOML file."""
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file does not exist: {config_path}"
        )

    with config_path.open("rb") as file:
        return tomllib.load(file)

config = load_config(CONFIG_PATH)
output_config = config["outputs"]

st.title("NYC Taxi Validator")
st.write(
    "Review Parquet files, profile results, sample records, "
    "and validation findings."
)

default_data_in = "./data_in"
default_data_out = "./data_out"

st.subheader("Project Paths")

source_col, output_col = st.columns(2)

with source_col:
    source_directory = st.text_input(
        "Source directory",
        value=default_data_in,
    )

with output_col:
    output_directory = st.text_input(
        "Output directory",
        value=default_data_out,
    )

data_in = Path(source_directory).expanduser().resolve()
data_out = Path(output_directory).expanduser().resolve()

stop_request_path = (
    data_out / config["control"]["stop_request"]
)

if not data_in.exists():
    st.error("The source directory does not exist.")
    st.stop()

if not data_in.is_dir():
    st.error("The source path is not a directory.")
    st.stop()

if not data_out.exists():
    st.error("The output directory does not exist.")
    st.stop()

if not data_out.is_dir():
    st.error("The output path is not a directory.")
    st.stop()

parquet_files = sorted(data_in.glob("*.parquet"))

progress_path = data_out / output_config["progress"]
event_log_path = data_out / output_config["event_log"]
errors_path = data_out / output_config["errors"]
summary_path = data_out / output_config["summary"]
execution_log_path = data_out / output_config["execution_log"]

st.metric(
    "Parquet files discovered",
    len(parquet_files),
)

if not parquet_files:
    st.warning("No Parquet files were found in the source directory.")
    st.stop()

file_names = [file_path.name for file_path in parquet_files]

selected_file_name = st.selectbox(
    "Select a Parquet file",
    options=file_names,
)

selected_file = data_in / selected_file_name

file_size_mb = selected_file.stat().st_size / (1024 * 1024)

st.subheader("Selected File")

file_col, size_col = st.columns(2)

file_stat = selected_file.stat()
parquet_file = pq.ParquetFile(selected_file)

file_size_mb = file_stat.st_size / (1024 * 1024)
modified_at = datetime.fromtimestamp(file_stat.st_mtime)

metadata = parquet_file.metadata

st.subheader("Selected File Metadata")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "File size",
    f"{file_size_mb:,.1f} MB",
)

col2.metric(
    "Rows",
    f"{metadata.num_rows:,}",
)

col3.metric(
    "Columns",
    f"{metadata.num_columns:,}",
)

col4.metric(
    "Row groups",
    f"{metadata.num_row_groups:,}",
)

st.write(f"**Filename:** `{selected_file.name}`")
st.write(f"**Full path:** `{selected_file}`")
st.write(
    f"**Last modified:** "
    f"{modified_at:%Y-%m-%d %H:%M:%S}"
)

with file_col:
    st.write(selected_file.name)

with size_col:
    st.metric(
        "File size",
        f"{file_size_mb:,.1f} MB",
    )

st.subheader("Parquet Schema")

schema_rows = [
    {
        "Column": field.name,
        "Arrow type": str(field.type),
        "Nullable": field.nullable,
    }
    for field in parquet_file.schema_arrow
]

st.dataframe(
    schema_rows,
    width="stretch",
    hide_index=True,
)
