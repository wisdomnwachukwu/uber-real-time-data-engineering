# Data Model Documentation

## 1. Purpose

This document describes the Silver One Big Table (OBT) and Gold
dimensional model used in the Uber data engineering project.

The Gold layer contains six dimensions and one fact table. Five
dimensions use SCD Type 1, while `dim_location` uses SCD Type 2 to
preserve historical versions.

> **Implementation note:** The table names and SCD strategies below
> reflect the project details provided. Confirm the exact fact-table
> name, table grain, keys, column names, and relationships against the
> implemented schemas before treating this document as a physical schema
> specification.

## 2. Modeling Overview

``` text
Batch ride data + real-time ride data
                  |
                  v
               stg_ride
                  |
                  | joins to mapping datasets
                  | SQL generated using Jinja
                  v
          Silver streaming OBT
                  |
                  v
       Gold source views / Auto CDC flows
                  |
       +----------+-----------+--------------------+
       |                      |                    |
       v                      v                    v
  Dimensions              Fact table          CDC handling
```

The OBT is an enriched Silver streaming table. It combines ride records
with attributes from mapping datasets and serves as the source for the
Gold dimensional model.

## 3. Silver Layer: One Big Table (OBT)

### Role

The OBT provides an enriched, consolidated representation of ride data
before it is transformed into the Gold dimensions and fact table.

### Inputs

-   The unified ride streaming table, `stg_ride`.
-   Mapping datasets read from the files loaded into ADLS Gen2.

### Transformation

Jinja generates SQL text for the joins between `stg_ride` and the
mapping datasets. The rendered SQL defines the streaming transformation
that creates the OBT.

The transformation uses a three-minute event-time watermark on
`booking_timestamp`.

### Modeling considerations

-   Confirm the intended grain of the OBT, for example, whether one row
    represents one ride or another business event.
-   Verify join keys and mapping coverage.
-   Check that mapping joins do not unexpectedly increase the number of
    ride rows.
-   Define how missing or invalid mapping values are represented.
-   Validate late-event and duplicate-event behaviour.

## 4. Gold Layer Tables

### Dimension summary

  -------------------------------------------------------------------------
  Table             Purpose             SCD strategy      History retained?
  ----------------- ------------------- ----------------- -----------------
  `dim_booking`     Booking-related     Type 1            Previous
                    descriptive                           attribute
                    attributes                            versions are not
                                                          retained by Type
                                                          1 handling

  `dim_driver`      Driver-related      Type 1            Previous
                    descriptive                           attribute
                    attributes                            versions are not
                                                          retained by Type
                                                          1 handling

  `dim_passenger`   Passenger-related   Type 1            Previous
                    descriptive                           attribute
                    attributes                            versions are not
                                                          retained by Type
                                                          1 handling

  `dim_payment`     Payment-related     Type 1            Previous
                    descriptive                           attribute
                    attributes                            versions are not
                                                          retained by Type
                                                          1 handling

  `dim_vehicle`     Vehicle-related     Type 1            Previous
                    descriptive                           attribute
                    attributes                            versions are not
                                                          retained by Type
                                                          1 handling

  `dim_location`    Location-related    Type 2            Historical
                    attributes                            versions are
                                                          retained
                                                          according to the
                                                          CDC configuration

  Fact table        Ride-related        As implemented    Confirm from the
                    measures and                          fact flow
                    dimension                             configuration
                    references                            
  -------------------------------------------------------------------------

The purpose descriptions are conceptual; document the exact columns and
business meaning from the actual table schemas.

## 5. SCD Type 1 Dimensions

The following dimensions use SCD Type 1:

-   `dim_booking`
-   `dim_driver`
-   `dim_passenger`
-   `dim_payment`
-   `dim_vehicle`

Type 1 handling updates the current dimensional representation when
tracked attributes change. It does not preserve prior versions of those
attributes in the dimension.

This is appropriate for attributes where the intended reporting
requirement is to use the latest state rather than reconstruct the
historical value.

### Validation checks

-   Verify that the configured business key uniquely identifies the
    intended dimension entity.
-   Test an update to a tracked attribute and confirm that the target
    reflects the latest value.
-   Check that repeated or out-of-order source changes behave as
    expected under the configured sequencing rules.
-   Confirm whether any attributes require historical tracking and
    should not be handled as Type 1.

## 6. SCD Type 2: `dim_location`

`dim_location` uses SCD Type 2 to retain historical versions of location
records.

When a tracked attribute changes, the intended behaviour is to retain
the previous version and create a new version according to the Auto CDC
configuration.

### Current-record identification

The project uses the `_END` column to identify current records:

``` sql
WHERE _END IS NULL
```

This filter selects current location versions for current-state queries.
It should not be applied indiscriminately to every historical
fact-to-dimension join, because doing so can remove the historical
version needed to describe an older ride.

### Historical relationship to facts

For accurate historical analysis, determine how the fact table
references location:

1.  **Surrogate-key approach:** The fact row stores the key of the
    correct historical `dim_location` version.
2.  **Effective-date join approach:** The query matches the ride's
    relevant timestamp to the validity interval of a location version.

Document the approach actually used. Do not assume the fact table
preserves historical location context unless the key assignment or join
logic supports it.

### Validation checks

-   Change a tracked location attribute and confirm that the prior
    version remains available.
-   Confirm that a new current version is created according to the CDC
    configuration.
-   Check that the intended current-record indicator is correct.
-   Validate that historical fact records resolve to the appropriate
    location version when historical reporting is required.
-   Test multiple changes to the same location entity and confirm the
    expected version sequence.

## 7. Fact Table

The project includes one Gold fact table. Its exact physical name,
grain, measures, and foreign keys should be documented from the
implemented schema.

### Document these properties

  -----------------------------------------------------------------------
  Property                            What to specify
  ----------------------------------- -----------------------------------
  Fact table name                     Exact target table name

  Grain                               What one row represents

  Business key                        Ride or event identifier, if
                                      applicable

  Measures                            Numeric values intended for
                                      aggregation

  Dimension keys                      Keys linking the fact to each
                                      relevant dimension

  Event timestamp                     Timestamp used for reporting and
                                      event-time analysis

  Change handling                     Actual Auto CDC or other
                                      update/append strategy

  Late-arriving data                  How late events and late dimension
                                      records are handled
  -----------------------------------------------------------------------

### Fact-to-dimension relationships

A typical dimensional model relates the fact table to relevant
dimensions through keys. The actual relationships must be confirmed from
the project's SQL and schemas.

Potential relationships to validate include booking, driver, passenger,
payment, vehicle, and location. Do not assume every dimension is joined
directly to the fact in the same way without checking the
implementation.

### Validation checks

-   Confirm the fact table's grain.
-   Check whether its intended business key is unique at that grain.
-   Validate foreign-key coverage against the dimensions.
-   Check for unexpected row multiplication in joins.
-   Verify that numeric measures aggregate as intended.
-   Validate historical location key assignment if applicable.

## 8. Source Views and Auto CDC

The Gold streaming tables are populated using Auto CDC flows with source
views.

The view defines the input records presented to a flow. The flow
configuration defines how changes are applied to the target.

For each target, document:

-   Source view name.
-   Target table name.
-   Business key(s).
-   Sequencing column or expression.
-   SCD type.
-   Tracked and excluded columns, where configured.
-   Delete handling, if configured.
-   Expectations or data quality rules, if configured.

Auto CDC correctness depends on appropriate keys, sequencing, and source
change semantics. A streaming-table target alone does not guarantee
correct CDC results.

## 9. Data Quality Rules to Consider

The following are suggested rules to implement and test:

-   Required business keys must not be null.
-   Required timestamps must be valid.
-   Dimension keys should resolve to the intended records.
-   Duplicate business events should be handled according to explicit
    rules.
-   Mapping joins should have understood match rates.
-   Numeric measures should satisfy business constraints.
-   `dim_location` should have the expected number of current versions
    per business key.
-   Fact-to-location joins should preserve historical meaning when
    required.
-   Auto CDC sequencing should be deterministic for changes to the same
    key.

Mark each rule as implemented only after it is present in the pipeline
and tested.

## 10. Schema Reference Template

Complete this table from the actual Databricks schemas.

  ---------------------------------------------------------------------------------
  Table             Business key   Important          SCD/change     Source view
                                   attributes         strategy       
  ----------------- -------------- ------------------ -------------- --------------
  `dim_booking`     To document    To document        SCD Type 1     To document

  `dim_driver`      To document    To document        SCD Type 1     To document

  `dim_passenger`   To document    To document        SCD Type 1     To document

  `dim_payment`     To document    To document        SCD Type 1     To document

  `dim_vehicle`     To document    To document        SCD Type 1     To document

  `dim_location`    To document    Include            SCD Type 2     To document
                                   validity/history                  
                                   columns                           

  Fact table        To document    Measures and       As implemented To document
                                   dimension keys                    
  ---------------------------------------------------------------------------------

## 11. Summary

The model separates enrichment from analytics: the Silver OBT joins
unified ride data with mapping datasets, while the Gold layer organizes
the result into six dimensions and one fact table. SCD Type 1 is used
for five dimensions, and SCD Type 2 preserves location history. The
remaining documentation task is to fill in the physical schemas, grain,
keys, source views, and exact fact relationships from the implemented
pipeline.
