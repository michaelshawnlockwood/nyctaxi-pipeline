---
layout: page
title: "Run Steps"
---

# Run Steps – NYC Taxi Pipeline

This page summarizes the pipeline phases and links to detailed steps.

- **Phase 1 & 2: Validation + Conversion**  
  See [Validation Steps](validation_steps) for schema/profile checks, conversion to PSV, and dictionary generation.

- **Phase 3: Load into SQL Server**  
  Coming next — creating `CREATE TABLE` scripts and loading PSV with `BULK INSERT`.

- **Phase 4: Load into PostgreSQL**  
  Coming next — using `COPY FROM` for PSV import.

- **Phase 5+: Orchestration / Analytics**  
  Future: Airflow DAGs, Databricks medallion layers, Power BI reporting.
