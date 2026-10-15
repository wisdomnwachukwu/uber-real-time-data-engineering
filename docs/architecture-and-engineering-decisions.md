### **4.1 Problem statement**
The objective was to build an end-to-end data pipeline that integrates real-time ride events with historical ride records and reference mapping data.
The pipeline needed to support different ingestion patterns, combine datasets into a consistent structure, enrich records with mapping attributes, and produce an analytical dimensional model.
The architecture also needed to accommodate changes in dimension records, including preserving location history where required.
The solution was implemented using Azure services and Databricks.

### **4.2 Why separate batch and streaming ingestion?**
The project has two input paths.
Input	Ingestion path	Reason
Real-time Uber events	Event Hubs → Databricks	Supports continuous event ingestion
Initial ride data	GitHub → ADF → ADLS Gen2 → Databricks	Supports file-based ingestion
Mapping files	GitHub → ADF → ADLS Gen2 → Databricks	Makes reference files available for processing


This separation reflects the different characteristics of the inputs.
Streaming events arrive over time, while the initial files are loaded as discrete datasets.
The two paths can be developed and monitored independently before their data is combined downstream.
Trade-off: Maintaining separate ingestion paths introduces additional components and operational responsibilities. However, it allows each path to use an ingestion method appropriate to its source.

### **4.3 Why combine batch and streaming data in stg_ride?**
The initial batch dataset provides historical ride records, while Event Hubs provides real-time events.
I used append-flow processing to combine the two datasets into stg_ride.
The purpose is to create a unified downstream input so that the subsequent transformation does not need to treat historical and newly arriving rides as completely separate datasets.
This approach requires careful consideration of schema compatibility, duplicate records, and the relationship between historical records and streaming events.
For example, if the historical file contains a ride that also appears in the event stream, the pipeline needs an appropriate business-key and deduplication strategy if the two records represent the same ride.
Append processing alone does not establish that records are unique.

### **4.4 Why use Jinja-generated SQL?**
The pipeline uses a Jinja template to generate SQL for joining stg_ride with the mapping datasets.
This separates the configuration used to construct the transformation from the SQL text ultimately executed by the pipeline.
The approach can improve maintainability when joins share common structures or when multiple mapping datasets must be incorporated consistently.
However, generated SQL introduces its own responsibilities.
The rendered output must be validated to ensure that:
- Join conditions are correct.
- The intended join type is used.
- Mapping keys have the expected data types.
- Unexpected nulls are handled appropriately.
- The joins do not unintentionally multiply ride records.
The key engineering lesson is that templating reduces repetitive code, but it does not replace testing the generated SQL.

### **4.5 Why create a Silver OBT?**
The One Big Table serves as an enriched intermediate dataset between unified ride ingestion and the Gold dimensional model.
The OBT combines ride data with attributes from the mapping datasets.
This provides a common source for the downstream dimension and fact transformations.
It also separates two responsibilities:
**1.** Integrating and enriching source data.
**2.** Organizing the enriched data into an analytical model.
Trade-off: A wide OBT can simplify downstream transformations, but it may duplicate attributes across records and can become expensive to maintain. Its usefulness depends on the downstream model and the cost of repeating the source joins.

### **4.6 Why use a three-minute watermark?**
The OBT streaming transformation uses a three-minute event-time watermark on booking_timestamp.
Event time represents when an event occurred, rather than when the processing system received it.
This distinction matters when events arrive later than expected.
Watermarking allows supported streaming operations to manage state based on event-time progress.
However, a three-minute watermark is a design parameter, not a universal rule. Its suitability depends on the actual arrival-delay distribution and the requirements for handling late events.
I would validate this choice by examining how frequently events arrive more than three minutes after their booking timestamps and determining what behaviour is expected for those records.
For stream-stream joins, the applicable join type and watermark configuration also influence state retention and late-data handling.

### **4.7 Why use Spark Declarative Pipelines?**
The project uses Spark Declarative Pipelines to define streaming datasets and their transformations.
The declarative approach allows the engineer to describe the desired processing logic while the platform manages supported aspects of execution.
Depending on the dataset type and configuration, the framework can handle incremental processing, streaming progress, and other operational details.
The engineering responsibility does not disappear. Source definitions, keys, sequencing, schema handling, data quality, and recovery behaviour still require deliberate design.
The benefit is that the pipeline implementation can focus on expressing the intended transformations rather than manually implementing every aspect of streaming execution.

### **4.8 Why use Auto CDC flows?**
The Gold tables are populated through Auto CDC flows using source views.
The source views define the records presented to the flows. The CDC configuration determines how changes are applied to the target tables.
This separates the construction of the input dataset from the handling of changes in the target dimension or fact table.
For CDC to produce correct results, the source data must provide the information required by the configured processing logic, including appropriate keys and sequencing information.
The implementation should also be tested for duplicate changes, out-of-order changes, and repeated processing.

### **4.9 Why SCD Type 1 for five dimensions?**
The following dimensions use Type 1 change handling:
- dim_booking
- dim_driver
- dim_passenger
- dim_payment
- dim_vehicle
The design objective is to maintain the latest dimensional state without retaining every previous attribute version.
This is appropriate when historical changes to those particular attributes are not required for the intended analytical use cases.
The decision is based on the information the model needs to preserve, rather than on a rule that certain dimension types must always use SCD Type 1.

### **4.10 Why SCD Type 2 for location?**
The location dimension uses SCD Type 2 to preserve historical versions of location records.
When a tracked location attribute changes, the intended model retains the previous version and creates a new current version.
The _END column identifies current records when _END IS NULL.
This supports current-state queries, but historical analysis requires appropriate relationships between facts and the correct dimension versions.
For example, a historical ride should reference the location version that was valid for that ride if the analytical requirement is to report using historical location attributes.
This requires the fact table to store the appropriate historical surrogate key or the query to use an appropriate effective-date join.

### **4.11 Data quality and reliability improvements**
The next development phase should focus on validating the assumptions made by the pipeline.
Priority checks include:
Area	Validation
Source ingestion	Verify expected data arrives from both paths
Ride identifiers	Identify missing or duplicate business keys
Timestamps	Validate required timestamps and event-time behaviour
Mapping joins	Detect missing matches and unexpected row multiplication
Streaming union	Check schema compatibility and duplicate ride handling
Watermarking	Evaluate the impact of events arriving later than three minutes
SCD Type 1	Verify that applicable dimensions reflect the intended latest state
SCD Type 2	Verify historical versions and uniqueness of current records
Fact relationships	Validate that foreign keys reference the intended dimension records
Pipeline recovery	Test failure recovery and repeated processing


These checks should be implemented according to the actual schema and business requirements.

### **4.12 Conclusion**
The project demonstrates how different ingestion patterns can be integrated into a unified data processing architecture.
Azure Event Hubs provides the real-time ingestion path, while Azure Data Factory and ADLS Gen2 support file-based ingestion.
Databricks combines the inputs, generates enriched transformations through Jinja-rendered SQL, and produces a Silver OBT that feeds the Gold dimensional model.
The Gold layer applies different change-handling strategies based on the intended historical requirements of the dimensions.
The next stage is to strengthen the pipeline with explicit data quality rules, testing, monitoring, and recovery validation.