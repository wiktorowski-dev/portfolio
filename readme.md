# Portfolio Projects

## Overview

This repository is a personal engineering portfolio showcasing projects in **backend development**, **data engineering**, and **cloud integration**. Each subdirectory contains a self-contained example that demonstrates skills in these domains, from building cloud-enabled APIs to performing data analysis on real-world datasets.

## Projects

* **`api/simple_aws_auth_with_rate_limit`** – A FastAPI-based REST API that integrates AWS Cognito for user authentication and enforces IP-based rate limiting. It uses AWS Secrets Manager and a MySQL database to persist user data, illustrating a combination of cloud identity services with application-level security controls.
* **`data-processing/polars-example`** – A Jupyter Notebook demonstrating high-performance data processing using the Polars library. It analyzes a NYC taxi trips dataset (fetched via Kaggle) and correlates it with local weather data, showcasing efficient SQL-like queries, window functions, and data visualization with Plotly.
* **`data-processing/pyspark-example`** – A Jupyter Notebook demonstrating scalable data processing using PySpark. It replicates the logic from the polars-example by analyzing NYC taxi trips (via Kaggle) and merging the data with local weather records. The project showcases distributed SQL-like queries, aggregation techniques, and weekday-based analysis using Spark DataFrames, culminating in visualizations created with Plotly. This highlights PySpark's capability for handling large datasets in a distributed environment.
