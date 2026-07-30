import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any
import streamlit as st
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_SCRIPT = PROJECT_ROOT / "pydantic_model_validator_v1.1.py"
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


def read_event_records(
    event_log_path: Path,
) -> list[dict[str, Any]]:
    """Read file-state records from the validation event log."""

    if not event_log_path.exists():
        return []

    records: list[dict[str, Any]] = []

    with event_log_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                st.warning(
                    f"Invalid JSON in {event_log_path.name} "
                    f"at line {line_number}."
                )

    return records


config = load_config(CONFIG_PATH)

st.title("Validation Control")
st.write(
    "Configure, launch, stop, and observe model validation."
)

default_data_in = "./data_in"
default_data_out = "./data_out"

source_directory, output_directory = st.columns(2)

with source_directory:
    source_directory = st.text_input(
        "Source directory",
        value=default_data_in,
    )

with output_directory:
    output_directory = st.text_input(
        "Output directory",
        value=default_data_out,
    )

extension_col, batch_size_col = st.columns(2)

with extension_col:
    extension = st.text_input(
        "File extension",
        value=".parquet",
    )

with batch_size_col:
    batch_size = st.number_input(
        "Batch size",
        min_value=1,
        value=50_000,
        step=10_000,
    )

data_in = Path(source_directory).expanduser().resolve()
data_out = Path(output_directory).expanduser().resolve()

progress_path = (
    data_out / config["outputs"]["progress"]
)

event_log_path = (
    data_out / config["outputs"]["event_log"]
)

stop_request_path = (
    data_out / config["control"]["stop_request"]
)

if "validator_process" not in st.session_state:
    st.session_state.validator_process = None

process = st.session_state.validator_process

validator_running = (
    process is not None
    and process.poll() is None
)

stop_requested = stop_request_path.exists()

start_col, stop_col = st.columns(2)

with start_col:
    start_clicked = st.button(
        "Start validation",
        type="primary",
        width="stretch",
    )

with stop_col:
    stop_clicked = st.button(
    "Request stop",
    width="stretch",
    disabled=not validator_running or stop_requested,
)

if start_clicked:
    process = st.session_state.validator_process

    if process is not None and process.poll() is None:
        st.warning("Validation is already running.")
    else:
        if stop_request_path.exists():
            stop_request_path.unlink()

        command = [
            sys.executable,
            str(VALIDATOR_SCRIPT),
            str(data_in),
            "--output-dir",
            str(data_out),
            "--extension",
            extension,
            "--batch-size",
            str(batch_size),
        ]

        st.session_state.validator_process = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
        )

        st.success("Validation started.")
        st.rerun()

        

if stop_clicked:
    stop_request_path.touch()

    st.session_state.stop_message = (
        "Stop requested. Validation will stop after the current batch."
    )

    st.rerun()


@st.fragment(run_every="1s")
def display_validation_events(
    event_log_path: Path,
) -> None:
    """Display the latest durable status for each validated file."""

    st.subheader("Validation File Status")

    records = read_event_records(event_log_path)

    if not records:
        st.info("No validation file events have been recorded.")
        return

    latest_by_file: dict[str, dict[str, Any]] = {}

    for record in records:
        filename = record.get("file")

        if isinstance(filename, str):
            latest_by_file[filename] = record

    st.dataframe(
        list(latest_by_file.values()),
        width="stretch",
        hide_index=True,
        height=360,
    )


@st.fragment(run_every="1s")
def display_validation_progress(
    progress_path: Path,
) -> None:
    """Display recent records from the validation progress file."""

    records = read_progress_records(progress_path)

    if not records:
        st.info("No validation progress has been recorded.")
        return

    recent_records = records[-5:]

    st.subheader("Validation Progress")
    # st.markdown("**Validation Progress**")

    st.json(
        recent_records,
        expanded=True,
    )


@st.fragment(run_every="1s")
def display_validator_status() -> None:
    """Display the current validator process status."""

    process = st.session_state.validator_process

    if process is None:
        st.info("Validation has not been started.")

    elif process.poll() is None:
        if stop_request_path.exists():
            st.warning(
                "Stop requested. "
                "Validation will stop after the current batch."
            )
        else:
            st.info("Validation is running.")

    elif process.returncode == 0:
        st.session_state.pop("stop_message", None)
        st.success("Validation process ended.")

    else:
        st.session_state.pop("stop_message", None)
        st.error(
            f"Validation process exited with code "
            f"{process.returncode}."
        )


display_validator_status()

display_validation_progress(progress_path)

display_validation_events(event_log_path)

