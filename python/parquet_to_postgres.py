from __future__ import annotations

import argparse
import io
import os
from pathlib import Path
from time import perf_counter

import pandas as pd
import pyarrow.parquet as pq
import psycopg
from dotenv import load_dotenv

from psycopg import sql
from typing import TypedDict


COLUMN_MAP = {
    "VendorID": "vendor_id",
    "tpep_pickup_datetime": "tpep_pickup_datetime",
    "tpep_dropoff_datetime": "tpep_dropoff_datetime",
    "passenger_count": "passenger_count",
    "trip_distance": "trip_distance",
    "RatecodeID": "ratecode_id",
    "store_and_fwd_flag": "store_and_fwd_flag",
    "PULocationID": "pu_location_id",
    "DOLocationID": "do_location_id",
    "payment_type": "payment_type",
    "fare_amount": "fare_amount",
    "extra": "extra",
    "mta_tax": "mta_tax",
    "tip_amount": "tip_amount",
    "tolls_amount": "tolls_amount",
    "improvement_surcharge": "improvement_surcharge",
    "total_amount": "total_amount",
    "congestion_surcharge": "congestion_surcharge",
    "Airport_fee": "airport_fee",
}

INTEGER_COLUMNS = [
    "vendor_id",
    "passenger_count",
    "ratecode_id",
    "pu_location_id",
    "do_location_id",
    "payment_type",
]

SOURCE_COLUMNS = list(COLUMN_MAP.keys())
TARGET_COLUMNS = list(COLUMN_MAP.values())


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Load NYC Taxi Parquet files into PostgreSQL "
            "using bounded batches and COPY."
        )
    )

    parser.add_argument(
        "data_in",
        type=Path,
        help="Directory containing source files.",
    )

    parser.add_argument(
        "--extension",
        default=".parquet",
        help="Source file extension. Default: .parquet",
    )

    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path("postgres_.env"),
        help="PostgreSQL environment file.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=50_000,
        help="Rows processed per batch. Default: 50000",
    )

    parser.add_argument(
        "--table",
        default="bronze.yellow_tripdata",
        help="Target PostgreSQL relation.",
    )

    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate the target table before loading.",
    )

    return parser.parse_args()


def normalize_extension(extension: str) -> str:
    return extension if extension.startswith(".") else f".{extension}"


def discover_files(
    data_in: Path,
    extension: str,
) -> list[Path]:
    if not data_in.exists():
        raise FileNotFoundError(
            f"Input directory does not exist: {data_in}"
        )

    if not data_in.is_dir():
        raise NotADirectoryError(
            f"Input path is not a directory: {data_in}"
        )

    files = sorted(data_in.glob(f"*{extension}"))

    if not files:
        raise FileNotFoundError(
            f"No {extension} files found in {data_in}"
        )

    return files


def load_postgres_configuration(
    env_file: Path,
) -> PostgresConfiguration:
    if not env_file.exists():
        raise FileNotFoundError(
            f"Environment file does not exist: {env_file}"
        )

    load_dotenv(env_file)

    required_variables = [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DATABASE",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]

    missing_variables = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing_variables:
        raise ValueError(
            "Missing PostgreSQL environment variables: "
            f"{', '.join(missing_variables)}"
        )

    return {
        "host": os.environ["POSTGRES_HOST"],
        "port": int(os.environ["POSTGRES_PORT"]),
        "dbname": os.environ["POSTGRES_DATABASE"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "sslmode": os.getenv("POSTGRES_SSLMODE", "prefer"),
    }


def validate_source_schema(
    parquet_file: pq.ParquetFile,
    file_path: Path,
) -> None:
    available_columns = set(
        parquet_file.schema_arrow.names
    )

    missing_columns = set(SOURCE_COLUMNS) - available_columns

    if missing_columns:
        raise ValueError(
            f"{file_path.name} is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    unexpected_columns = available_columns - set(SOURCE_COLUMNS)

    if unexpected_columns:
        print(
            f"  Additional columns will be ignored: "
            f"{sorted(unexpected_columns)}"
        )


def dataframe_to_csv_buffer(
    dataframe: pd.DataFrame,
) -> io.StringIO:
    buffer = io.StringIO()

    dataframe.to_csv(
        buffer,
        index=False,
        header=False,
        na_rep=r"\N",
        lineterminator="\n",
    )

    buffer.seek(0)

    return buffer


def load_parquet_file(
    connection: psycopg.Connection,
    file_path: Path,
    target_table: str,
    batch_size: int,
) -> int:
    parquet_file = pq.ParquetFile(file_path)

    validate_source_schema(
        parquet_file=parquet_file,
        file_path=file_path,
    )

    schema_name, table_name = target_table.split(".", maxsplit=1)

    copy_sql = sql.SQL(
        """
        COPY {}.{} ({})
        FROM STDIN
        WITH (
            FORMAT CSV,
            NULL '\\N'
        )
        """
    ).format(
        sql.Identifier(schema_name),
        sql.Identifier(table_name),
        sql.SQL(", ").join(
            sql.Identifier(column)
            for column in TARGET_COLUMNS
        ),
    )

    rows_loaded = 0
    file_started_at = perf_counter()

    print(
        f"\nLoading {file_path.name} "
        f"({parquet_file.metadata.num_rows:,} rows)"
    )

    for batch_number, record_batch in enumerate(
        parquet_file.iter_batches(
            batch_size=batch_size,
            columns=SOURCE_COLUMNS,
        ),
        start=1,
    ):
        dataframe = record_batch.to_pandas()

        dataframe = dataframe.rename(
            columns=COLUMN_MAP
        )

        dataframe = dataframe[TARGET_COLUMNS]

        for column in INTEGER_COLUMNS:
            dataframe[column] = dataframe[column].astype("Int64")

        csv_buffer = dataframe_to_csv_buffer(dataframe)

        with connection.cursor() as cursor:
            with cursor.copy(copy_sql) as copy:
                while csv_chunk := csv_buffer.read(1_048_576):
                    copy.write(csv_chunk)

        batch_rows = len(dataframe)
        rows_loaded += batch_rows

        print(
            f"  Batch {batch_number:,}: "
            f"{batch_rows:,} rows "
            f"({rows_loaded:,} total)"
        )

    elapsed_seconds = perf_counter() - file_started_at

    print(
        f"Completed {file_path.name}: "
        f"{rows_loaded:,} rows in "
        f"{elapsed_seconds:,.2f} seconds"
    )

    return rows_loaded

class PostgresConfiguration(TypedDict):
    host: str
    port: int
    dbname: str
    user: str
    password: str
    sslmode: str

def main() -> None:
    args = parse_arguments()

    data_in = args.data_in.expanduser().resolve()
    env_file = args.env_file.expanduser().resolve()
    extension = normalize_extension(args.extension)

    files = discover_files(
        data_in=data_in,
        extension=extension,
    )

    postgres_configuration = load_postgres_configuration(
        env_file=env_file,
    )

    print(f"Input directory: {data_in}")
    print(f"Files discovered: {len(files)}")
    print(f"Target relation: {args.table}")
    print(f"Batch size: {args.batch_size:,}")

    total_rows_loaded = 0
    load_started_at = perf_counter()

    with psycopg.connect(
        host=postgres_configuration["host"],
        port=postgres_configuration["port"],
        dbname=postgres_configuration["dbname"],
        user=postgres_configuration["user"],
        password=postgres_configuration["password"],
        sslmode=postgres_configuration["sslmode"],
    ) as connection:
        if args.truncate:
            print(
                f"Truncating {args.table} before loading."
            )

            schema_name, table_name = args.table.split(
                ".",
                maxsplit=1,
            )

            truncate_sql = sql.SQL(
                "TRUNCATE TABLE {}.{}"
            ).format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
            )

            with connection.cursor() as cursor:
                cursor.execute(truncate_sql)

            connection.commit()

        for file_path in files:
            rows_loaded = load_parquet_file(
                connection=connection,
                file_path=file_path,
                target_table=args.table,
                batch_size=args.batch_size,
            )

            connection.commit()
            total_rows_loaded += rows_loaded

    elapsed_seconds = perf_counter() - load_started_at

    print("\nLoad completed.")
    print(f"Files loaded: {len(files)}")
    print(f"Rows loaded: {total_rows_loaded:,}")
    print(
        f"Elapsed time: {elapsed_seconds:,.2f} seconds"
    )


if __name__ == "__main__":
    main()