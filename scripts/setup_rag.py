import os
import time
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.exceptions import AlreadyExists

def create_data_store():
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    location = "global"
    ds_id = "underwriter-loss-runs"
    
    client = discoveryengine.DataStoreServiceClient()
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
    
    print(f"Checking if Data Store '{ds_id}' exists...")
    try:
        store = client.get_data_store(name=f"{parent}/dataStores/{ds_id}")
        print(f"Data Store '{ds_id}' already exists!")
        return f"{parent}/dataStores/{ds_id}"
    except Exception:
        print(f"Data Store '{ds_id}' does not exist. Creating...")
        
    data_store = discoveryengine.DataStore(
        display_name="Underwriter Loss Runs",
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )
    
    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store_id=ds_id,
        data_store=data_store,
    )
    
    operation = client.create_data_store(request=request)
    print("Waiting for Data Store creation to complete (this may take up to 10 minutes)...")
    response = operation.result()
    print(f"Successfully created Data Store: {response.name}")
    
    # Wait extra time for the datastore backend pipeline to boot up before uploading
    print("Waiting 30 seconds for backend indexing infrastructure to initialize...")
    time.sleep(30)
    return response.name

def upload_documents(parent_ds):
    doc_client = discoveryengine.DocumentServiceClient()
    directory = "reports"
    
    for filename in os.listdir(directory):
        if not filename.endswith(".pdf"):
            continue
            
        client_name = filename.split("_")[0]
        file_path = os.path.join(directory, filename)
        
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
            
        print(f"Uploading {client_name} loss runs with custom metadata...")
        
        doc = discoveryengine.Document(
            id=client_name,
            struct_data={
                "title": f"{client_name.capitalize()} Loss Runs Report",
                "client_id": client_name,
                "document_type": "loss_runs"
            },
            content=discoveryengine.Document.Content(
                mime_type="application/pdf",
                raw_bytes=pdf_bytes
            )
        )
        
        request = discoveryengine.CreateDocumentRequest(
            parent=f"{parent_ds}/branches/0",
            document=doc,
            document_id=client_name
        )
        
        try:
            # Delete the existing document if it exists so we can reseed the metadata
            doc_client.delete_document(name=f"{parent_ds}/branches/0/documents/{client_name}")
            print(f"Purged stale document for {client_name}.")
        except Exception:
            pass
            
        try:
            doc_client.create_document(request=request)
            print(f"Successfully uploaded {client_name} Document with metadata.")
        except AlreadyExists:
            print(f"Document {client_name} already exists (deletion failed?). Skipping.")
        except Exception as e:
            print(f"Failed to upload {client_name}: {e}")

if __name__ == "__main__":
    ds_name = create_data_store()
    upload_documents(ds_name)
    print("\nData Store Seeding Complete!")
    print("Note: Indexing the uploaded documents for semantic search may take 15-30 minutes on GCP's backend.")
