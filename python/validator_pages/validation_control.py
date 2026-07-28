import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any
import streamlit as st


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

config = load_config(CONFIG_PATH)

st.title("Validation Control")
st.write(
    "Configure, launch, stop, and observe model validation."
)

default_data_in = "./data_in"
default_data_out = "./data_out"

source_directory = st.text_input(
    "Source directory",
    value=default_data_in,
)

output_directory = st.text_input(
    "Output directory",
    value=default_data_out,
)

extension = st.text_input(
    "File extension",
    value=".parquet",
)

batch_size = st.number_input(
    "Batch size",
    min_value=1,
    value=50_000,
    step=10_000,
)

data_in = Path(source_directory).expanduser().resolve()
data_out = Path(output_directory).expanduser().resolve()

stop_request_path = (
    data_out / config["control"]["stop_request"]
)

if "validator_process" not in st.session_state:
    st.session_state.validator_process = None

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
    )

if start_clicked:
    process = st.session_state.validator_process

    if process is not None and process.poll() is None:
        st.warning("Validation is already running.")
    else:
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

if stop_clicked:
    stop_request_path.touch()

    st.warning(
        "Stop requested. Validation will stop after the current batch."
    )

process = st.session_state.validator_process

if process is None:
    st.info("Validation has not been started.")
elif process.poll() is None:
    st.info("Validation is running.")
elif process.returncode == 0:
    st.success("Validation process finished.")
else:
    st.error(
        f"Validation process exited with code {process.returncode}."
    )
