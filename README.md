# NYC Taxi Data Pipeline

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![SQL Server](https://img.shields.io/badge/SQL%20Server-2019-red?logo=microsoftsqlserver)
![SQL Server](https://img.shields.io/badge/SQL%20Server-2022-red?logo=microsoftsqlserver)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-Orchestration-success?logo=apacheairflow)
![Databricks](https://img.shields.io/badge/Databricks-Lakehouse-orange?logo=databricks)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboards-yellow?logo=powerbi)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

This project builds a **reproducible data pipeline** for the NYC Taxi & Limousine Commission (TLC) trip records dataset.  
It demonstrates how raw data can be ingested, validated, transformed, and made analytics-ready across multiple platforms.

---

## ✨ Features
- **Ingestion**: Bulk import of TLC Parquet → PSV/CSV → SQL Server & PostgreSQL  
- **Validation**: Python scripts for schema and data quality checks  
- **Transformation**: SQL stored procedures + Airflow DAGs  
- **Analytics**: Aggregations in SQL Server / Databricks (Delta Lake / Medallion architecture)  
- **Visualization**: Power BI dashboards for insights  

---

## 📂 Repository Structure

![Repository Structure](docs/repo-structure.svg)

