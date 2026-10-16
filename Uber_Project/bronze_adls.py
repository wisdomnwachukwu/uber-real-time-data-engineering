# Databricks notebook source
import pandas as pd

files = [
{"file":"map_cities"},
{"file":"map_cancellation_reasons"},
{"file":"map_payment_methods"},
{"file":"map_ride_statuses"},
{"file":"map_vehicle_makes"},
{"file":"map_vehicle_types"}
]
for file in files:
    url = f"https://uberstorageaccount.blob.core.windows.net/raw/ingestion/{file['file']}.json?sp=r&st=2026-10-16T00:53:53Z&se=2026-10-20T09:08:53Z&spr=https&sv=2026-02-06&sr=c&sig=1AronDZINOsP9wNbVZ3KU5eOsEqGejaioQW8GW%2BTgII%3D"

    df = pd.read_json(url)
    df_spark = spark.createDataFrame(df)
    
    # Writing data to the bronze layer
    df_spark.write.format("delta")\
        .option("overwriteSchema", "true")\
            .mode("overwrite")\
                .saveAsTable(f"Uber.bronze.{file['file']}")


# COMMAND ----------

url = "https://uberstorageaccount.blob.core.windows.net/raw/ingestion/bulk_rides.json?sp=r&st=2026-10-16T00:53:53Z&se=2026-10-20T09:08:53Z&spr=https&sv=2026-02-06&sr=c&sig=1AronDZINOsP9wNbVZ3KU5eOsEqGejaioQW8GW%2BTgII%3D"

df = pd.read_json(url)
df_spark = spark.createDataFrame(df)
if not spark.catalog.tableExists("uber.bronze.bulk_rides"):
    df_spark.write.format("delta")\
            .mode("overwrite")\
            .saveAsTable(f"Uber.bronze.bulk_rides")
    print("This will not run more than 1 time")