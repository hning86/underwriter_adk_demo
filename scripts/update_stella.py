from google.cloud import bigquery
import os

def main():
    client = bigquery.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "ninghai-ccai"))
    query = """
        UPDATE `ninghai-ccai.underwriter_demo.client_profiles`
        SET client_id = 'stella'
        WHERE client_id = 'retail'
    """
    client.query(query).result()
    print("Updated BQ successfully")

if __name__ == "__main__":
    main()
