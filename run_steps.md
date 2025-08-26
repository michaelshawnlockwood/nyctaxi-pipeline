# Run Steps – NYC Taxi Pipeline

This document describes how to validate, convert, and prepare NYC Taxi trip data for downstream SQL use.

---

## Prereqs

- Activate venv from repo root:
  - **PowerShell**
    ```powershell
    .\.venv\Scripts\Activate.ps1
    ```
  - **Git Bash**
    ```bash
    source .venv/Scripts/activate
    ```
- Install dependencies:
  ```bash
  pip install --upgrade pip
  pip install -r requirements.txt

- Installed: `duckdb`, `pandas`, `pyarrow`

---

## Phase 1 — Validate Input Parquet Files

Validates each `.parquet` in `data_in/` and writes:
- `_schema.txt` — column order + types  
- `_profile.csv` — null counts, example, min/max (numeric/date)  
- `_preview.csv` — first N rows (default 100)  
- `validation_summary.csv` — one line per file with rows + status

### Run (choose one)

**PowerShell**
```powershell
# Everything, non-recursive
python .\validate_parquet_batch.py "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_in"

# Recursive, skip files already validated
python .\validate_parquet_batch.py "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_in" --recursive --skip-existing

# Subset (example: Feb files)
python validate_parquet_batch.py "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_in"
python validate_parquet_batch.py "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_in" --recursive --skip-existing
python validate_parquet_batch.py "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_in" --pattern "yellow_tripdata_2024-02*.parquet"

# Outputs
Per-file: _schema.txt, _profile.csv, _preview.csv
Rollup: validation_summary.csv

## Phase 2 — Validate Input Parquet Files
Converts .parquet → .psv (pipe-separated). Produces one .psv per input and a rollup summary.

**PowerShell**
```powershell
# Full conversion (overwrite existing files)
python .\parquet_to_psv.py "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_in" --recursive --out-dir "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_out" --overwrite

# Sample conversion (limit rows, clearly flagged as LIMITED in summary)
python .\parquet_to_psv.py "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_in" --recursive --limit 50000 --out-dir "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_out" --overwrite

**bash**
python parquet_to_psv.py "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_in" --recursive --out-dir "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_out" --overwrite
python parquet_to_psv.py "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_in" --recursive --limit 50000 --out-dir "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_out" --overwrite

# Outputs
- `.psv` per `.parquet` in `data_out/`
- `psv_conversion_summary.csv` (columns: file, source_rows, written_rows, limit, status, out)

---

## Phase 2b — Validate PSV Files

Checks `.psv` outputs for schema consistency and row counts.

**PowerShell**
```powershell
python .\validate_psv.py "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_out\yellow_tripdata_2024-01.psv"
python .\validate_psv_batch.py "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_out" --recursive

**bash**
python validate_psv.py "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_out/yellow_tripdata_2024-01.psv"
python validate_psv_batch.py "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_out" --recursive

# Outputs
Per-file: _schema.txt, _profile.csv, _preview.csv
Rollup: psv_validation_summary.csv

## Phase 2.5 — Generate Unified Data Dictionary
Creates a single authoritative schema file for the dataset. Month suffix dropped from the name.

**Powershell**
python .\make_data_dictionary.py "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_out"

**bash**
python make_data_dictionary.py "D:/AppDev/nyctaxi/nyctaxi-pipeline/data_out"

# Outputs
yellow_tripdata.dictionary.csv
yellow_tripdata.dictionary.md (requires tabulate)

## Phase 3 — Load to SQL Server / PostgreSQL (Coming Next)
Generate CREATE TABLE scripts from the dictionary.
Bulk load PSV files:
SQL Server → BULK INSERT or OPENROWSET(BULK ...)
PostgreSQL → COPY table FROM STDIN WITH (FORMAT csv, DELIMITER '|', HEADER true)

