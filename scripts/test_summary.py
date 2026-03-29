import os
from google.cloud import discoveryengine_v1 as discoveryengine

def search():
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    search_client = discoveryengine.SearchServiceClient()
    serving_config = f"projects/{project_id}/locations/global/collections/default_collection/dataStores/underwriter-loss-runs/servingConfigs/default_search"
    
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query="Extract EVERY single claim row including the incident description, paid amount, and reserves.",
        page_size=1,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=1,
                include_citations=True
            )
        )
    )
    response = search_client.search(request)
    if response.summary:
        print("SUMMARY:", response.summary.summary_text)

search()
