import streamlit as st
from pathlib import Path
import pyarrow.parquet as pq
import json
import tomllib
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "validator" / "config.toml"


def load_config(config_path: Path) -> dict[str, Any]:
    """Load validator configuration from a TOML file."""
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file does not exist: {config_path}"
        )

    with config_path.open("rb") as file:
        return tomllib.load(file)


def read_progress_records(
    progress_path: Path,
) -> list[dict[str, Any]]:
    """Read structured validation-progress records from JSON Lines."""

    if not progress_path.exists():
        return []

    records: list[dict[str, Any]] = []

    with progress_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                st.warning(
                    f"Invalid JSON in {progress_path.name} "
                    f"at line {line_number}."
                )

    return records


config = load_config(CONFIG_PATH)

st.title("Validation Analytics")

# st.button("Refresh")

default_data_in = "./data_in"
default_data_out = "./data_out"

data_in = Path(default_data_in).expanduser().resolve()
data_out = Path(default_data_out).expanduser().resolve()

progress_path = (
    data_out / config["outputs"]["progress"]
)

event_log_path = data_out / config["outputs"]["event_log"]

button_col1, button_col2, button_col3 = st.columns(3)

with button_col1:
    if st.button("Reset progress log"):
        progress_path.write_text("", encoding="utf-8")
        st.rerun()

with button_col2:
    if st.button("Reset event log"):
        event_log_path.write_text("", encoding="utf-8")
        st.rerun()

with button_col3:
    if st.button("Reset validation state"):
        progress_path.write_text("", encoding="utf-8")
        event_log_path.write_text("", encoding="utf-8")
        st.rerun()

data_in = Path("./data_in").resolve()
parquet_files = sorted(data_in.glob("*.parquet"))

file_row_counts = [
    {
        "File": file_path.name,
        "Rows": pq.ParquetFile(file_path).metadata.num_rows,
    }
    for file_path in parquet_files
]

st.dataframe(
    file_row_counts,
    width="stretch",
    hide_index=True,
)

total_rows = sum(
    file_record["Rows"]
    for file_record in file_row_counts
)

poll_seconds = st.slider(
    "Refresh interval (seconds)",
    min_value=1,
    max_value=10,
    value=3,
    step=1,
)


@st.fragment(run_every=poll_seconds)
def show_live_analytics():
    progress_records = read_progress_records(progress_path)

    batch_records = [
        record
        for record in progress_records
        if record.get("event_type") == "batch_completed"
    ]

    batches_completed = len(batch_records)

    latest_record_by_file: dict[str, dict[str, Any]] = {}

    for record in batch_records:
        file_name = record["file"]

        if (
            file_name not in latest_record_by_file
            or record["recorded_at"]
            > latest_record_by_file[file_name]["recorded_at"]
        ):
            latest_record_by_file[file_name] = record

    rows_completed = sum(
        record["rows_processed"]
        for record in latest_record_by_file.values()
    )

    progress_ratio = rows_completed / total_rows if total_rows else 0

    col1, col2, col3 = st.columns(3)

    col1.metric(
        label="Rows validated",
        value=f"{rows_completed:,}",
    )

    col2.metric(
        label="Total rows",
        value=f"{total_rows:,}",
    )

    col3.metric(
        label="Batches completed",
        value=f"{batches_completed:,}",
    )

    st.progress(
        progress_ratio,
        text=f"{progress_ratio:.1%} of all rows validated",
    )

    st.subheader("Memory Usage")

    latest_batch_record = max(
        batch_records,
        key=lambda record: record["recorded_at"],
        default=None,
    )

    memory_files = sorted(
        {
            record["file"]
            for record in batch_records
            if "memory_mb" in record
        }
    )

    if not memory_files:
        st.info("No memory-usage records have been recorded.")
        return

    current_file = (
            latest_batch_record["file"]
            if latest_batch_record
            else memory_files[0]
        )

    default_file_index = memory_files.index(current_file)

    follow_current_file = st.checkbox(
        "Follow current file",
        value=True,
        key="follow_current_file",
    )

    if follow_current_file:
        selected_memory_file = current_file
        st.write(f"Current file: `{selected_memory_file}`")
    else:
        selected_memory_file = st.selectbox(
            "Select file",
            options=memory_files,
            index=default_file_index,
            key="memory_file",
        )

    memory_records = [
        {
            "Batch": record["batch_number"],
            "Memory (MB)": record["memory_mb"],
        }
        for record in batch_records
        if record["file"] == selected_memory_file
    ]

    st.line_chart(
        memory_records,
        x="Batch",
        y="Memory (MB)",
    )

    st.dataframe(
        memory_records,
        width="stretch",
        hide_index=True,
    )


show_live_analytics()