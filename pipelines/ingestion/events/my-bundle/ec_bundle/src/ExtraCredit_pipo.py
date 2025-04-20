# Databricks notebook source
# Import modules

import dlt
from pyspark.sql.functions import *

# Assign pipeline parameters to variables

my_catalog = spark.conf.get("my_catalog")
my_schema = spark.conf.get("my_schema")
my_volume = spark.conf.get("my_volume")

# Define the path to source data

volume_path = f"/Volumes/{my_catalog}/{my_schema}/{my_volume}/"

# Define a streaming table to ingest data from a volume

@dlt.table(
  comment="Popular baby first names in New York. This data was ingested from the New York State Department of Health."
)
def baby_names_raw():
  df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("inferSchema", True)
    .option("header", True)
    .load(volume_path)
  )
  df_renamed_column = df.withColumnRenamed("First Name", "First_Name")
  return df_renamed_column

# Define a materialized view that validates data and renames a column

@dlt.table(
  comment="New York popular baby first name data cleaned and prepared for analysis."
)
@dlt.expect("valid_first_name", "First_Name IS NOT NULL")
@dlt.expect_or_fail("valid_count", "Count > 0")
def baby_names_prepared():
  return (
    spark.read.table("baby_names_raw")
      .withColumnRenamed("Year", "Year_Of_Birth")
      .select("Year_Of_Birth", "First_Name", "Count")
  )

# Define a materialized view that has a filtered, aggregated, and sorted view of the data

@dlt.table(
  comment="A table summarizing counts of the top baby names for New York for 2021."
)
def top_baby_names_2021():
  return (
    spark.read.table("baby_names_prepared")
      .filter(expr("Year_Of_Birth == 2021"))
      .groupBy("First_Name")
      .agg(sum("Count").alias("Total_Count"))
      .sort(desc("Total_Count"))
      .limit(10)
  )