# Databricks notebook source
# MAGIC %md
# MAGIC ### **Jinja Template for OBT**

# COMMAND ----------

from pathlib import Path
from jinja2 import Template

# COMMAND ----------

Jinja_config = [
    {
        "table" : "Uber.bronze.stg_rides stg_rides",
        "from_clause": """
            STREAM(Uber.bronze.stg_rides)
            WATERMARK booking_timestamp
            DELAY OF INTERVAL 3 MINUTES stg_rides
        """,
        "select" : "stg_rides.ride_id, stg_rides.confirmation_number, stg_rides.passenger_id, stg_rides.driver_id, stg_rides.vehicle_id, stg_rides.pickup_location_id, stg_rides.dropoff_location_id, stg_rides.vehicle_type_id, stg_rides.vehicle_make_id, stg_rides.payment_method_id, stg_rides.ride_status_id, stg_rides.pickup_city_id, stg_rides.dropoff_city_id, stg_rides.cancellation_reason_id, stg_rides.passenger_name, stg_rides.passenger_email, stg_rides.passenger_phone, stg_rides.driver_name, stg_rides.driver_rating, stg_rides.driver_phone, stg_rides.driver_license, stg_rides.vehicle_model, stg_rides.vehicle_color, stg_rides.license_plate, stg_rides.pickup_address, stg_rides.pickup_latitude, stg_rides.pickup_longitude, stg_rides.dropoff_address, stg_rides.dropoff_latitude, stg_rides.dropoff_longitude, stg_rides.distance_miles, stg_rides.duration_minutes, stg_rides.booking_timestamp, stg_rides.pickup_timestamp, stg_rides.dropoff_timestamp, stg_rides.base_fare, stg_rides.distance_fare, stg_rides.time_fare, stg_rides.surge_multiplier, stg_rides.subtotal, stg_rides.tip_amount, stg_rides.total_fare, stg_rides.rating",
        "where" : ""
    },
    {
        "table" : "Uber.bronze.map_vehicle_makes map_vehicle_makes",
        "select" : "map_vehicle_makes.vehicle_make",
        "where" : "",
        "on" : "stg_rides.vehicle_make_id = map_vehicle_makes.vehicle_make_id"
    },
    {
        "table" : "Uber.bronze.map_vehicle_types map_vehicle_types",
        "select" : "map_vehicle_types.vehicle_type,map_vehicle_types.description,map_vehicle_types.base_rate,map_vehicle_types.per_mile,map_vehicle_types.per_minute",
        "where" : "",
        "on" : "stg_rides.vehicle_type_id = map_vehicle_types.vehicle_type_id"
    },
    {
        "table" : "Uber.bronze.map_ride_statuses map_ride_statuses",
        "select" : "map_ride_statuses.ride_status",
        "where" : "",
        "on" : "stg_rides.ride_status_id = map_ride_statuses.ride_status_id"
    },
    {
        "table" : "Uber.bronze.map_payment_methods map_payment_methods",
        "select" : "map_payment_methods.payment_method, map_payment_methods.is_card, map_payment_methods.requires_auth",
        "where" : "",
        "on" : "stg_rides.payment_method_id = map_payment_methods.payment_method_id"
    },
    {
        "table" : "Uber.bronze.map_cities map_cities",
        "select" : "map_cities.city as pickup_city,map_cities.state,map_cities.region",
        "where" : "",
        "on" : "stg_rides.pickup_city_id = map_cities.city_id"
    },
    {
        "table" : "Uber.bronze.map_cancellation_reasons map_cancellation_reasons",
        "select" : "map_cancellation_reasons.cancellation_reason",
        "where" : "",
        "on" : "stg_rides.cancellation_reason_id = map_cancellation_reasons.cancellation_reason_id"
    },
    
]

# COMMAND ----------

Jinja_str = """
    SELECT
        {% for config in Jinja_config %}
            {{config.select}}
                {% if not loop.last %}
                    ,
                {% endif %}
            {% endfor %}
    FROM
       {% for config in Jinja_config %}
            {% if loop.first %}
                 {{ config.from_clause }}
            {% else %}
                 LEFT JOIN {{ config.table }} ON {{ config.on }}
            {% endif %}
        {% endfor %}

        {% for config in Jinja_config %}
            {% if config.where != "" %}
            WHERE
            {% endif %}
            {{config.where}}
                {% if not loop.last %}
                    {% if config.where != "" %}
                        AND
                    {% endif %}
                {% endif %}
        {% endfor %}
"""


# COMMAND ----------

# 1. Render the Jinja template
sql_prefix = """
CREATE OR REFRESH STREAMING TABLE Uber.silver.silver_obt
AS
"""

rendered_template = (
    sql_prefix.strip()
    + "\n"
    + Template(Jinja_str).render(
        Jinja_config=Jinja_config
    ).strip()
)

# 2. Specify the pipeline SQL file
output_path = Path(
    "/Workspace/Users/wisdomnwex1404@gmail.com/"
    "Uber_Project/Uber_rides_ingest/"
    "transformations/silver_obt.sql"
)

# 3. Check whether the destination file exists
if not output_path.is_file():
    raise FileNotFoundError(
        f"Pipeline SQL file not found: {output_path}"
    )

# 4. Save the generated SQL
output_path.write_text(
    rendered_template + "\n",
    encoding="utf-8"
)

# 5. Confirm what was written
print(f"Generated SQL saved to: {output_path}")
print(rendered_template)


# COMMAND ----------

# MAGIC %md
# MAGIC