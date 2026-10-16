# Data Flow Documentation

## 1. Purpose

This document describes how data moves through the Uber data engineering
project, from source systems to the Gold dimensional model.

The implementation combines two ingestion paths:

-   A real-time path for Uber application events through Azure Event
    Hubs.
-   A batch path for the initial `bulk_rides.json` file and mapping
    files, delivered through Azure Data Factory to Azure Data Lake
    Storage Gen2 (ADLS Gen2).

The two paths converge in Databricks at the unified ride-processing
stage.

## 2. High-Level Flow

``` text
REAL-TIME PATH
Uber application events
        |
        v
Azure Event Hubs
        |
        v
Azure Databricks / Spark Declarative Pipelines
        |
        v
Unified ride streaming input: stg_ride
        ^
        |
BATCH PATH
GitHub files (bulk_rides.json + mapping files)
        |
        v
Azure Data Factory
        |
        v
Azure Data Lake Storage Gen2
        |
        v
Azure Databricks reads the files
        |
        +------------------------------+

stg_ride + mapping datasets
        |
        v
Jinja-generated SQL for streaming joins
        |
        v
Silver streaming table: One Big Table (OBT)
        |
        v
Source views
        |
        v
Auto CDC flows
        |
        v
Gold streaming tables: six dimensions + one fact table
```

This is a logical view of the data flow. Use the actual table and
pipeline names from the Databricks workspace when updating the diagram.

## 3. Real-Time Ingestion: Event Hubs to Databricks

1.  Uber application events are published to Azure Event Hubs.
2.  Spark Declarative Pipelines ingests the events into the Databricks
    processing flow.
3.  The real-time ride data is made available to the downstream unified
    ride stage.

In this implementation, Event Hubs is shown as the direct real-time
source for Databricks. The architecture does not show Event Hubs events
being landed in ADLS Gen2 before Databricks consumes them, because that
is not the described ingestion path.

## 4. Batch Ingestion: GitHub to ADLS Gen2

1.  The initial `bulk_rides.json` file and mapping files are maintained
    in GitHub.
2.  Azure Data Factory extracts and loads those files into ADLS Gen2.
3.  Databricks reads the files from ADLS Gen2 for processing.

ADLS Gen2 is the landing/storage location for these files in the
described implementation. Do not represent it as a mandatory
intermediate store for Event Hubs events unless that additional
persistence flow is implemented.

## 5. Unified Ride Input: `stg_ride`

The initial batch ride data and the real-time ride data are appended
into the streaming table named `stg_ride` using append-flow processing
in Spark Declarative Pipelines.

This gives the downstream transformation a common ride input rather than
requiring all subsequent logic to be duplicated for batch and real-time
records.

### Design considerations

-   **Schema compatibility:** The batch and streaming records need
    compatible schemas or an explicit alignment step.
-   **Duplicate handling:** Append processing by itself does not
    guarantee uniqueness. If a ride can appear in both the initial file
    and the event stream, apply and test an appropriate business-key and
    deduplication strategy if needed.
-   **Replay behaviour:** Confirm how source replays and pipeline
    restarts affect records in the target table.

## 6. Silver Layer: Jinja-Generated OBT

A Jinja template generates the SQL text used to join `stg_ride` with the
mapping datasets. The rendered SQL defines the streaming transformation
that creates the One Big Table (OBT).

The OBT is a **Silver streaming table** and feeds the Gold dimension and
fact flows.

The transformation uses a three-minute event-time watermark on
`booking_timestamp`.

### Why use Jinja?

Jinja allows reusable SQL patterns and join configuration to be
separated from the final rendered SQL. The generated SQL should still be
reviewed and tested for correct join conditions, join types, data types,
null handling, and unexpected row multiplication.

### Watermark considerations

A watermark helps supported streaming operations manage event-time state
and late-arriving data. A three-minute watermark is a configuration
choice, not a guarantee that every event arriving more than three
minutes late will be included. Actual behaviour depends on the streaming
operation, watermark configuration, and late-data requirements.

Validate the selected interval against the event-lateness distribution
and the project's completeness requirements.

## 7. Gold Layer: Auto CDC Flows

The Gold layer contains six dimensions and one fact table. The tables
are implemented as streaming tables and are populated through Auto CDC
flows using source views.

The source views define the data supplied to each flow. The Auto CDC
configuration determines how changes are applied to the target, based on
the configured keys, sequencing, and SCD behaviour.

  Target            Change strategy
  ----------------- -----------------------------------------------------
  `dim_booking`     SCD Type 1
  `dim_driver`      SCD Type 1
  `dim_passenger`   SCD Type 1
  `dim_payment`     SCD Type 1
  `dim_vehicle`     SCD Type 1
  `dim_location`    SCD Type 2
  Fact table        Confirm and document the configured change strategy

For `dim_location`, `_END IS NULL` identifies current records in the
described model. This filter is appropriate for current-state queries;
historical joins must use the correct historical key or effective-date
logic when historical attributes are required.

## 8. Operational and Data Quality Checks

Recommended checks to add or document as they are implemented:

-   Validate required ride identifiers and timestamps.
-   Check schema compatibility between batch and streaming inputs.
-   Identify duplicate ride records where business rules require
    uniqueness.
-   Measure unmatched mapping records.
-   Check whether mapping joins multiply ride rows unexpectedly.
-   Monitor late-event behaviour relative to the three-minute watermark.
-   Validate Auto CDC keys and sequencing.
-   Verify that only the intended current location version has
    `_END IS NULL`.
-   Test recovery, replay, and repeated processing.
-   Monitor pipeline failures and data quality violations.

These are recommendations for validation and future hardening; they
should not be described as implemented until verified in the project.

## 9. Downstream Consumption

The Gold layer is structured for analytical use. A BI tool such as Power
BI can be documented as a downstream consumer once it is connected and
configured.

## 10. Summary

The pipeline separates real-time and batch ingestion, unifies ride
records in `stg_ride`, enriches them in a Silver streaming OBT using
Jinja-generated SQL, and feeds a Gold dimensional model through Auto CDC
flows. This design provides a foundation for incremental processing and
analytical workloads, with data quality, late-data handling,
deduplication, monitoring, and recovery testing as important validation
areas.
