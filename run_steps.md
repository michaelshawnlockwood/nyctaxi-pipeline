# Run Steps – NYC Taxi Pipeline

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
python .\validate_parquet_batch.py "D:\AppDev\nyctaxi\nyctaxi-pipeline\data_in" --pattern "yellow_tripdata_2024-02*.parquet"
