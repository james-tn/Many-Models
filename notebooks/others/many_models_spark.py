# Databricks notebook source
# MAGIC %md ## Prepare data from Microsoft Open Dataset

# COMMAND ----------

# MAGIC %md https://azure.microsoft.com/en-us/services/open-datasets/catalog/sample-oj-sales-simulated

# COMMAND ----------

data =spark.read.format("csv").option("header", True).load("wasbs://ojsales-simulatedcontainer@azureopendatastorage.blob.core.windows.net/oj_sales_data/Store10*.csv")

# COMMAND ----------

#Write to local delta for fast reading
data.write.format("delta").saveAsTable("OJ_Sales_Data")

# COMMAND ----------

# MAGIC %sql select * from OJ_Sales_Data

# COMMAND ----------

# MAGIC %sql select count (distinct store, brand) from OJ_Sales_Data 

# COMMAND ----------

# MAGIC %sql select distinct brand from OJ_Sales_Data

# COMMAND ----------

# MAGIC %md ## Pre-training exersize

# COMMAND ----------

# MAGIC %md
# MAGIC 1. Read about Pandas Function APIs: https://docs.microsoft.com/en-us/azure/databricks/spark/latest/spark-sql/pandas-function-apis
# MAGIC 2. Answer following questions:
# MAGIC - What is the advantage of this technology vs. regular Python UDF?
# MAGIC - What is the role of Apache Arrow in this?
# MAGIC - What is the use of iterator and yield vs. regular list and return?
# MAGIC 
# MAGIC     

# COMMAND ----------

# MAGIC %md 
# MAGIC Using the OJ sales dataset above, use Pandas Function APIs, pick out for each store and brand the best selling week in the form of week_number-yyyy.
# MAGIC The result set look like this:

# COMMAND ----------

import pandas as pd
result_sample= pd.DataFrame({"store": [1066, 1067, 1068],'Brand':['dominicks', 'tropicana','tropicana'],"Best_Selling_Week": ['23-1992', '24-1991','24-1991']})
display(result_sample)

# COMMAND ----------

# MAGIC %md #Optional reading: we'll  following forecast models from the Many Models repo

# COMMAND ----------

https://github.com/microsoft/solution-accelerator-many-models/blob/master/Custom_Script/scripts/timeseries_utilities.py
https://github.com/microsoft/solution-accelerator-many-models/blob/master/Custom_Script/scripts/train.py
https://github.com/microsoft/solution-accelerator-many-models/blob/master/Custom_Script/scripts/forecast.py