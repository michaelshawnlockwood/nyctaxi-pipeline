from __future__ import annotations
import argparse
from pathlib import Path
from dataclasses import dataclass
import json
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel
import pyarrow.parquet as pq
import os
import psutil
import gc


@dataclass(frozen=True)
class OutputPaths:
    execution_log: Path # what the script did, for people reading the log
    event_log: Path # structured file-state events used for restart and resume
    errors: Path # detailed row-validation failures
    summary: Path # aggregate validation results per file


class TaxiTrip(BaseModel):
    VendorID: int
    tpep_pickup_datetime: datetime
    tpep_dropoff_datetime: datetime
    passenger_count: int | None
    trip_distance: float
    RatecodeID: int | None
    store_and_fwd_flag: str | None
    PULocationID: int
    DOLocationID: int
    payment_type: int
    fare_amount: float
    extra: float
    mta_tax: float
    tip_amount: float
    tolls_amount: float
    improvement_surcharge: float
    total_amount: float
    congestion_surcharge: float | None
    Airport_fee: float | None
    cbd_congestion_fee: float | None = None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate every matching file in a directory "
            "against a Pydantic model."
        ),
        epilog="""
    Examples:

    Validate all Parquet files using the default extension:
        py validate_file_against_pydantic_model.py ../data_in

    Specify the file extension and output directory:
        py validate_file_against_pydantic_model.py ../data_in --extension .parquet --output-dir ../data_out

    Simulate a failure for restart testing:
        py validate_file_against_pydantic_model.py ../data_in --output-dir ../data_out --fail-on yellow_tripdata_2024-04.parquet
    """,
                formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "source_dir",
        type=Path,
        help="Directory containing the files to validate.",
    )

    parser.add_argument(
        "--extension",
        default=".parquet",
        help="File extension to process. Default: .parquet",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("../data_out"),
        help="Directory for validation output files. Default: ../data_out",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=50_000,
        help="Number of Parquet rows to read per batch. Default: 50000",
    )

    parser.add_argument(
        "--fail-on",
        help=(
            "Intentionally fail when this filename is reached. "
            "Used to test restart behavior."
        ),
    )

    return parser.parse_args()

def normalize_extension(extension: str) -> str:
    """Ensure that the file extension begins with a period."""
    extension = extension.strip()

    if not extension:
        raise ValueError("The file extension cannot be empty.")

    if not extension.startswith("."):
        extension = f".{extension}"

    return extension.lower()

# File discovery
def discover_files(
    source_dir: Path,
    extension: str,
) -> list[Path]:
    """Return matching files from the source directory."""
    if not source_dir.exists():
        raise FileNotFoundError(
            f"Source directory does not exist: {source_dir}"
        )

    if not source_dir.is_dir():
        raise NotADirectoryError(
            f"Source path is not a directory: {source_dir}"
        )

    matching_files = sorted(
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() == extension
    )

    return matching_files


def prepare_output_paths(output_dir: Path) -> OutputPaths:
    """Create the output directory and return its file paths."""
    output_dir.mkdir(parents=True, exist_ok=True)

    return OutputPaths(
        execution_log=output_dir / "pydantic_validation.log",
        event_log=output_dir / "validation_event_log.jsonl",
        errors=output_dir / "validation_errors.jsonl",
        summary=output_dir / "validation_summary.jsonl",
    )


def utc_now() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append one JSON object to a JSON Lines file."""
    with path.open("a", encoding="utf-8") as file:
        json.dump(record, file, ensure_ascii=False, default=str)
        file.write("\n")
        file.flush()


def load_latest_statuses(
    event_log_path: Path,
) -> dict[str, dict[str, Any]]:
    """Return the most recent event_log record for each file."""
    latest: dict[str, dict[str, Any]] = {}

    if not event_log_path.exists():
        return latest

    with event_log_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {event_log_path} "
                    f"at line {line_number}."
                ) from error

            filename = record.get("file")

            if isinstance(filename, str):
                latest[filename] = record

    return latest


def validate_file(
    file_path: Path,
    batch_size: int,
) -> None:
    """Read and validate one Parquet file in batches."""
    parquet_file = pq.ParquetFile(file_path)
    process = psutil.Process(os.getpid())
    rows_processed = 0

    for batch_number, batch in enumerate(
        parquet_file.iter_batches(batch_size=batch_size),
        start=1,
    ):
        records = batch.to_pylist()

        for record in records:
            TaxiTrip.model_validate(record)

        rows_processed += len(records)

        memory_mb = process.memory_info().rss / (1024 * 1024)

        print(
            f"  Batch {batch_number:,}: "
            f"{rows_processed:,} rows validated; "
            f"memory: {memory_mb:,.1f} MB"
        )

        # Explicitly release the batch-related objects after each progress message:
        del records
        del batch
        gc.collect()


def main() -> None:
    args = parse_args()

    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    extension = normalize_extension(args.extension)

    batch_size = args.batch_size

    if batch_size <= 0:
        raise ValueError("Batch size must be greater than zero.")

    files = discover_files(
        source_dir=source_dir,
        extension=extension,
    )

    output_paths = prepare_output_paths(output_dir)

    latest_statuses = load_latest_statuses(
        output_paths.event_log
    )

    print(f"Source directory: {source_dir}")
    print(f"Output directory: {output_dir}")
    print(f"File extension: {extension}")
    print(f"Files discovered: {len(files):,}")
    print(f"Batch size: {batch_size:,}")

    for file_path in files:
        previous_status = latest_statuses.get(file_path.name)

        if (
            previous_status
            and previous_status.get("status") == "completed"
        ):
            print(f"Skipping completed file: {file_path.name}")
            continue

        print(f"Processing: {file_path.name}")

        # Record that processing has begun.
        append_jsonl(
            output_paths.event_log,
            {
                "file": file_path.name,
                "status": "started",
                "started_at": utc_now(),
            },
        )

        try:
            # Temporary failure test.
            if (
                args.fail_on
                and file_path.name == args.fail_on
            ):
                raise RuntimeError(
                    f"Simulated failure for {file_path.name}"
                )

            # Pydantic row validation.
            validate_file(
                file_path=file_path,
                batch_size=batch_size,
            )

            # Record successful completion.
            append_jsonl(
                output_paths.event_log,
                {
                    "file": file_path.name,
                    "status": "completed",
                    "completed_at": utc_now(),
                },
            )

            print(f"Completed: {file_path.name}")

        except KeyboardInterrupt:
            append_jsonl(
                output_paths.event_log,
                {
                    "file": file_path.name,
                    "status": "interrupted",
                    "interrupted_at": utc_now(),
                },
            )

            print(f"Interrupted: {file_path.name}")
            return

        except Exception as error:
            # Record the failure before the program exits.
            append_jsonl(
                output_paths.event_log,
                {
                    "file": file_path.name,
                    "status": "failed",
                    "error": str(error),
                    "failed_at": utc_now(),
                },
            )

            print(f"Failed: {file_path.name}: {error}")
            raise


if __name__ == "__main__":
    main()