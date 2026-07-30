import streamlit as st
from pathlib import Path
import pyarrow.parquet as pq
import json
import tomllib
from typing import Any
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "validator" / "config.toml"

st.title("Trip Analytics")


def load_config(config_path: Path) -> dict[str, Any]:
    """Load validator configuration from a TOML file."""
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file does not exist: {config_path}"
        )

    with config_path.open("rb") as file:
        return tomllib.load(file)


config = load_config(CONFIG_PATH)

default_data_in = "./data_in"
default_data_out = "./data_out"

data_in = Path(default_data_in).expanduser().resolve()
data_out = Path(default_data_out).expanduser().resolve()

progress_path = (
    data_out / config["outputs"]["progress"]
)

data_in = Path("./data_in").resolve()
parquet_files = sorted(data_in.glob("*.parquet"))

if not parquet_files:
    st.warning("No Parquet files were found.")
    st.stop()

file_names = [file_path.name for file_path in parquet_files]

choose_files = st.checkbox(
    "Choose files",
    value=False,
)

if choose_files:
    selected_file_names = st.multiselect(
        "Select Parquet files",
        options=file_names,
        default=file_names,
    )

    selected_files = [
        data_in / file_name
        for file_name in selected_file_names
    ]
else:
    selected_files = parquet_files

if not selected_files:
    st.warning("Select at least one Parquet file.")
    st.stop()

st.metric(
    "Files selected",
    len(selected_files),
)

pickup_frames = []

for file_path in selected_files:
    table = pq.read_table(
        file_path,
        columns=["tpep_pickup_datetime"],
    )

    pickup_frames.append(table.to_pandas())

pickup_data = pd.concat(
    pickup_frames,
    ignore_index=True,
)

pickup_data["Pickup hour"] = (
    pickup_data["tpep_pickup_datetime"].dt.hour
)

trips_by_hour = (
    pickup_data
    .groupby("Pickup hour")
    .size()
    .reset_index(name="Trips")
    .sort_values("Pickup hour")
)

st.subheader("Trips by Pickup Hour")

st.bar_chart(
    trips_by_hour,
    x="Pickup hour",
    y="Trips",
)



