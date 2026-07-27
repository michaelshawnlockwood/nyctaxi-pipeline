from pathlib import Path
import streamlit as st
from datetime import datetime
import pyarrow.parquet as pq


st.set_page_config(
    page_title="NYC Taxi Validator",
    page_icon="🚕",
    layout="wide",
)

st.title("NYC Taxi Validator")
st.write(
    "Review Parquet files, profile results, sample records, "
    "and validation findings."
)

data_in = Path("../data_in").resolve()
data_out = Path("../data_out").resolve()

st.subheader("Project Paths")

source_col, output_col = st.columns(2)

with source_col:
    st.text_input(
        "Source directory",
        value=str(data_in),
        disabled=True,
    )

with output_col:
    st.text_input(
        "Output directory",
        value=str(data_out),
        disabled=True,
    )

parquet_files = sorted(data_in.glob("*.parquet"))

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
    use_container_width=True,
    hide_index=True,
)
