from __future__ import annotations

import argparse
from pathlib import Path
from dataclasses import dataclass
import json
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class OutputPaths:
    log: Path
    manifest: Path
    errors: Path
    summary: Path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate every matching file in a directory "
            "against a Pydantic model."
        )
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
        log=output_dir / "pydantic_validation.log",
        manifest=output_dir / "validation_manifest.jsonl",
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
    manifest_path: Path,
) -> dict[str, dict[str, Any]]:
    """Return the most recent manifest record for each file."""
    latest: dict[str, dict[str, Any]] = {}

    if not manifest_path.exists():
        return latest

    with manifest_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {manifest_path} "
                    f"at line {line_number}."
                ) from error

            filename = record.get("file")

            if isinstance(filename, str):
                latest[filename] = record

    return latest


def main() -> None:
    args = parse_args()

    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    extension = normalize_extension(args.extension)

    files = discover_files(
        source_dir=source_dir,
        extension=extension,
    )

    output_paths = prepare_output_paths(output_dir)

    latest_statuses = load_latest_statuses(
        output_paths.manifest
    )

    print(f"Source directory: {source_dir}")
    print(f"Output directory: {output_dir}")
    print(f"File extension: {extension}")
    print(f"Files discovered: {len(files):,}")

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
            output_paths.manifest,
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

            # Pydantic row validation will eventually go here.

            # Record successful completion.
            append_jsonl(
                output_paths.manifest,
                {
                    "file": file_path.name,
                    "status": "completed",
                    "completed_at": utc_now(),
                },
            )

            print(f"Completed: {file_path.name}")

        except Exception as error:
            # Record the failure before the program exits.
            append_jsonl(
                output_paths.manifest,
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