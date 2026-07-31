import streamlit as st
from pathlib import Path
import pyarrow.parquet as pq
import json
import tomllib
from typing import Any
import pandas as pd
from time import perf_counter
import duckdb
import streamlit.components.v1 as components


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "validator" / "config.toml"

TAXI_ZONES_PATH = (
    PROJECT_ROOT
    / "assets"
    / "data"
    / "taxi_zones_4326_v2.geojson"
)

from components.taxi_zone_choropleth import (
    render_taxi_zone_choropleth,
)

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

payment_type_labels = {
    0: "Flex Fare trip",
    1: "Credit card",
    2: "Cash",
    3: "No charge",
    4: "Dispute",
    5: "Unknown",
    6: "Voided trip",
}

st.subheader("Filter Trips by Payment Type")

select_all_col, select_none_col, _ = st.columns(3)

with select_all_col:
    select_all = st.button(
        "Select all",
        key="select_all_payment_types",
    )

with select_none_col:
    select_none = st.button(
        "Clear all",
        key="clear_all_payment_types",
    )

if select_all:
    for payment_code in payment_type_labels:
        st.session_state[f"payment_type_{payment_code}"] = True

if select_none:
    for payment_code in payment_type_labels:
        st.session_state[f"payment_type_{payment_code}"] = False

column_ct = 4

payment_columns = st.columns(column_ct)

selected_payment_types: list[int] = []

for index, (payment_code, payment_label) in enumerate(
    payment_type_labels.items()
):
    with payment_columns[index % column_ct]:
        if st.checkbox(
            payment_label,
            value=True,
            key=f"payment_type_{payment_code}",
        ):
            selected_payment_types.append(payment_code)


zone_map, payment_type, pandas_col, duckdb_col = st.columns(4)

with zone_map:
    show_pickup_map = st.button(
        "Show pickup-zone map",
        key="show_pickup_zone_map",
    )

with payment_type:
    run_payment_type = st.button(
        "Show trips by payment type",
        key="run_payment_type",
        type="primary",
    )

with pandas_col:
    run_pandas = st.button(
        "Run Pandas analysis",
    )

with duckdb_col:
    run_duckdb = st.button(
        "Run DuckDB analysis",
    )

if run_pandas:
  if not selected_payment_types:
      st.warning("Select at least one payment type.")
      st.stop()

  started_at = perf_counter()

  pickup_frames = []

  for file_path in selected_files:
      table = pq.read_table(
          file_path,
          columns=[
              "tpep_pickup_datetime",
              "payment_type",
          ],
      )

      pickup_frames.append(table.to_pandas())

  pickup_data = pd.concat(
      pickup_frames,
      ignore_index=True,
  )

  pickup_data = pickup_data[
      pickup_data["payment_type"].isin(
          selected_payment_types
      )
  ]

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

  elapsed_ms = (perf_counter() - started_at) * 1_000

  st.metric(
      "Pandas execution time",
      f"{elapsed_ms:,.1f} ms",
  )

  st.subheader("Trips by Pickup Hour — Pandas")

  st.bar_chart(
      trips_by_hour,
      x="Pickup hour",
      y="Trips",
  )


# show_pickup_map = st.button(
#     "Show pickup-zone map",
#     key="show_pickup_zone_map",
# )

if show_pickup_map:
    if not selected_payment_types:
        st.warning("Select at least one payment type.")
        st.stop()

    started_at = perf_counter()

    selected_file_paths: list[str] = [
        str(file_path)
        for file_path in selected_files
    ]
    
    connection = duckdb.connect()

    file_list_sql = ", ".join(
            f"'{file_path.replace("'", "''")}'"
            for file_path in selected_file_paths
        )

    payment_type_sql = ", ".join(
            str(payment_type)
            for payment_type in selected_payment_types
        )

    trips_by_zone = connection.sql(
        f"""
        SELECT
            PULocationID AS "LocationID",
            COUNT(*) AS "TripCount"
        FROM read_parquet([{file_list_sql}])
        WHERE payment_type IN ({payment_type_sql})
        AND PULocationID IS NOT NULL
        AND PULocationID > 0
        GROUP BY PULocationID
        ORDER BY PULocationID
        """
    ).df()

    trip_counts_by_location = dict(
        zip(
            trips_by_zone["LocationID"],
            trips_by_zone["TripCount"],
        )
    )

    with TAXI_ZONES_PATH.open("r", encoding="utf-8") as file:
        taxi_zones_geojson = json.load(file)

    for feature in taxi_zones_geojson["features"]:
        location_id = feature["properties"]["LocationID"]

        feature["properties"]["TripCount"] = int(
            trip_counts_by_location.get(location_id, 0)
        )

    render_taxi_zone_choropleth(
        taxi_zones_geojson,
    )

    components.html(
        """
        <div id="d3-test"></div>

        <style>
          .map-credit {
            margin-top: 8px;
            color: #9ca3af;
            font: 12px/1.4 system-ui, sans-serif;
            text-align: center;
          }
        </style>

        <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
        <script>
          const tooltip = d3.select("#taxi-zone-tooltip");
          d3.select("#d3-test")
            .append("p")
            .style("color", "white");
        </script>
        """,
        height=100,
    )

    connection.close()

    elapsed_ms = (perf_counter() - started_at) * 1_000

    st.metric(
        "DuckDB execution time",
        f"{elapsed_ms:,.1f} ms",
    )

    st.dataframe(
        trips_by_zone,
        width="stretch",
        hide_index=True,
    )

if run_duckdb:
    if not selected_payment_types:
        st.warning("Select at least one payment type.")
        st.stop()

    started_at = perf_counter()

    selected_file_paths: list[str] = [
        str(file_path)
        for file_path in selected_files
    ]

    connection = duckdb.connect()

    file_list_sql = ", ".join(
        f"'{file_path.replace("'", "''")}'"
        for file_path in selected_file_paths
    )

    payment_type_sql = ", ".join(
        str(payment_type)
        for payment_type in selected_payment_types
    )

    trips_by_hour = connection.sql(
        f"""
        SELECT
            CAST(
                EXTRACT(HOUR FROM tpep_pickup_datetime)
                AS INTEGER
            ) AS "Pickup hour",
            COUNT(*) AS "Trips"
        FROM read_parquet([{file_list_sql}])
        WHERE payment_type IN ({payment_type_sql})
        GROUP BY 1
        ORDER BY 1
        """
    ).df()

    connection.close()

    elapsed_ms = (perf_counter() - started_at) * 1_000

    st.metric(
        "DuckDB execution time",
        f"{elapsed_ms:,.1f} ms",
    )

    st.subheader("Trips by Pickup Hour — DuckDB")

    st.bar_chart(
        trips_by_hour,
        x="Pickup hour",
        y="Trips",
    )

if run_payment_type:
    started_at = perf_counter()

    selected_file_paths: list[str] = [
        str(file_path)
        for file_path in selected_files
    ]

    connection = duckdb.connect()

    file_list_sql = ", ".join(
        f"'{file_path.replace("'", "''")}'"
        for file_path in selected_file_paths
    )

    trips_by_payment_type = connection.sql(
        f"""
        SELECT
            CASE payment_type
                WHEN 0 THEN 'Flex Fare trip'
                WHEN 1 THEN 'Credit card'
                WHEN 2 THEN 'Cash'
                WHEN 3 THEN 'No charge'
                WHEN 4 THEN 'Dispute'
                WHEN 5 THEN 'Unknown'
                WHEN 6 THEN 'Voided trip'
                ELSE 'Other'
            END AS "Payment type",
            COUNT(*) AS "Trips"
        FROM read_parquet([{file_list_sql}])
        GROUP BY payment_type
        ORDER BY "Trips" DESC
        """
    ).df()

    connection.close()

    elapsed_ms = (perf_counter() - started_at) * 1_000

    st.metric(
        "DuckDB execution time",
        f"{elapsed_ms:,.1f} ms",
    )

    st.subheader("Trips by Payment Type")

    st.bar_chart(
        trips_by_payment_type,
        x="Payment type",
        y="Trips",
    )

