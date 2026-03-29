import os
from google.cloud import discoveryengine_v1 as discoveryengine

def search_ensemble(client_id: str):
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    search_client = discoveryengine.SearchServiceClient()
    serving_config = f"projects/{project_id}/locations/global/collections/default_collection/dataStores/underwriter-loss-runs/servingConfigs/default_search"
    
    queries = [
        f"What are the significant auto accident and warehouse incidents for {client_id}?",
        f"What are the highest paid claims, cargo damages, reserves, and payouts for {client_id}?",
        f"What are the safety violations, ergonomic issues, and worker compensation claims for {client_id}?"
    ]
    
    snippets = []
    
    for q in queries:
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=q,
            page_size=5,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True,
                    max_snippet_count=3
                )
            )
        )
        response = search_client.search(request)
        for result in response.results:
            if result.document.id != client_id:
                continue
            if result.document.derived_struct_data:
                for snip in result.document.derived_struct_data.get("snippets", []):
                    snippets.append(snip.get("snippet", ""))

    print(f"--- ENSEMBLE RESULTS FOR {client_id} ---")
    # Deduplicate
    unique_snips = list(set(snippets))
    for s in unique_snips:
        print(f"-> {s}")

search_ensemble("acme")
