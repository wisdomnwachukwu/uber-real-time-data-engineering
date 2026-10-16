# 🚗 End-to-End Uber Data Engineering Platform
### Real-Time Streaming, Batch Ingestion, CDC, and Dimensional Modeling on Azure Databricks

## 📌 Project Overview

This project implements an end-to-end data engineering pipeline that
integrates real-time ride events from an Uber application with historical
batch data and reference mapping files.

The solution combines Azure Event Hubs, Azure Data Factory, Azure Data Lake
Storage Gen2, and Azure Databricks to ingest, process, enrich, and transform
data into an analytical data model.

The pipeline uses Spark Declarative Pipelines to manage data processing,
a unified streaming table to combine historical and real-time ride data,
Jinja templates to generate reusable SQL transformations, and a
One Big Table (OBT) in the Silver layer to prepare enriched ride data
for downstream processing.

The Gold layer contains six dimension tables and one fact table. CDC-based
processing maintains the dimensional tables using SCD Type 1 and SCD Type 2
strategies.

The project demonstrates practical experience with real-time data
engineering, batch ingestion, cloud data integration, incremental
processing, event-time processing, change data capture, and dimensional
data modeling.

---

## 🎯 Engineering Problem

Operational applications generate data through different ingestion
patterns.

Real-time events may arrive continuously, while historical records and
reference files are delivered as batch data. These datasets must be
integrated into a consistent structure before they can support analytical
queries.

This project addresses several engineering challenges:

- Ingesting real-time events independently of historical file ingestion.
- Integrating batch ride records with continuously arriving events.
- Combining operational ride data with reference mapping files.
- Creating reusable transformation logic for multiple datasets.
- Managing incremental changes in downstream dimensional tables.
- Preserving historical changes in selected dimensions.
- Organizing processed data into a structure suitable for analytics.

The solution brings these responsibilities together in a unified
Azure-based data engineering architecture.

---

## 🏗️ Architecture

### 1. Real-Time Ingestion

Uber application events are published to Azure Event Hubs.

Azure Databricks consumes the events through Spark Declarative Pipelines
and processes them through the streaming ingestion path.

### 2. Batch Ingestion

The initial `bulk_rides.json` file and reference mapping files are stored
in GitHub.

Azure Data Factory extracts and loads these files into Azure Data Lake
Storage Gen2.

Databricks reads the stored files for downstream processing.

### 3. Unified Ride Processing

The batch ride data and real-time ride data are appended into a streaming
table named `stg_ride`.

This provides a unified input for downstream transformations.

### 4. Silver Layer — One Big Table (OBT)

A Jinja template generates SQL text used to configure joins between
`stg_ride` and the mapping datasets.

The resulting SQL creates the One Big Table (OBT), which is implemented
as a Silver streaming table.

The OBT enriches ride records with attributes obtained from the mapping
datasets and provides a common source for the Gold layer.

The streaming transformation uses a three-minute event-time watermark
on `booking_timestamp`.

### 5. Gold Layer — Dimensional Model

The Gold layer contains six dimensions and one fact table.

| Table | Description | Change Strategy |
|---|---|---|
| `dim_booking` | Booking dimension | SCD Type 1 |
| `dim_driver` | Driver dimension | SCD Type 1 |
| `dim_passenger` | Passenger dimension | SCD Type 1 |
| `dim_payment` | Payment dimension | SCD Type 1 |
| `dim_vehicle` | Vehicle dimension | SCD Type 1 |
| `dim_location` | Location dimension | SCD Type 2 |
| `fact_rides` | Ride fact table | As configured in the pipeline |

The Gold tables are implemented as streaming tables and populated through
Auto CDC flows using source views.

SCD Type 1 maintains the latest dimensional state for the applicable
dimensions.

SCD Type 2 preserves historical versions of location records.

---

## 📚 Documentation

- [Architecture and Engineering Decisions](docs/architecture-and-engineering-decisions.md)
- [Data Flow Documentation](docs/data-flow.md)
- [Data Model Documentation](docs/data-model.md)

## 🔄 Data Flow

```text
                         REAL-TIME PATH

                    Uber Application
                           |
                           v
                    Azure Event Hubs
                           |
                           v
                  Azure Databricks
               Spark Declarative Pipelines
                           |
                           |
                           v
                      stg_ride
                           ^
                           |
                           |
                          BATCH PATH

                         GitHub
                           |
                           v
                   Azure Data Factory
                           |
                           v
               Azure Data Lake Storage Gen2
                           |
                           v
                  Azure Databricks
                           |
                           |
                           v
                      stg_ride
                           |
                           v
                 Jinja-Generated SQL
                           |
                           v
                 Mapping Data Joins
                           |
                           v
                    Silver OBT
                           |
                           v
                    Gold Layer
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
    Dimensions          Fact Table      CDC Processing

    dim_booking         fact_rides
    dim_driver
    dim_passenger
    dim_payment
    dim_vehicle
    dim_location





