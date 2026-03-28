import os
from dotenv import load_dotenv
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

# Load environment variables
load_dotenv()

def main():
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "ninghai-ccai")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    client = bigquery.Client(project=project_id, location=location)

    dataset_id = f"{project_id}.underwriter_demo"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = location

    try:
        client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {dataset_id}")
    except Conflict:
        print(f"Dataset {dataset_id} already exists")

    table_id = f"{dataset_id}.client_profiles"
    
    # Drop table to ensure fresh schema and data
    client.delete_table(table_id, getattr(client, "not_found_ok", True) if hasattr(client, "not_found_ok") else None)
    try:
        client.delete_table(table_id, not_found_ok=True)
    except Exception:
        pass
        
    schema = [
        bigquery.SchemaField("client_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("industry", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("company_size", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("annual_revenue", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("headquarters", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("years_in_business", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("primary_operations", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("number_of_facilities", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("safety_rating_class", "STRING", mode="REQUIRED"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    try:
        table = client.create_table(table)
        print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Conflict:
        print(f"Table {table_id} already exists")

    rows_to_insert = [
        {
            "client_id": "acme",
            "name": "Acme Logistics",
            "industry": "Transportation",
            "company_size": 250,
            "annual_revenue": 50000000,
            "headquarters": "Chicago, IL",
            "years_in_business": 15,
            "primary_operations": "Freight Hauling & Last-Mile",
            "number_of_facilities": 2,
            "safety_rating_class": "Satisfactory"
        },
        {
            "client_id": "zenith",
            "name": "Zenith Manufacturing",
            "industry": "Heavy Machinery",
            "company_size": 1200,
            "annual_revenue": 300000000,
            "headquarters": "Detroit, MI",
            "years_in_business": 42,
            "primary_operations": "Industrial Equipment Assembly",
            "number_of_facilities": 4,
            "safety_rating_class": "Excellent"
        },
        {
            "client_id": "stella",
            "name": "Stellar Retail",
            "industry": "E-Commerce",
            "company_size": 800,
            "annual_revenue": 150000000,
            "headquarters": "Seattle, WA",
            "years_in_business": 8,
            "primary_operations": "E-Commerce & Warehousing",
            "number_of_facilities": 3,
            "safety_rating_class": "Satisfactory"
        }
    ]

    errors = client.insert_rows_json(table_id, rows_to_insert)
    if not errors:
        print("New rows have been added.")
    else:
        print(f"Encountered errors while inserting rows: {errors}")

if __name__ == "__main__":
    main()
