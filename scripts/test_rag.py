import os
import argparse
from google.cloud import discoveryengine_v1 as discoveryengine

def query_datastore(client_name: str):
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ninghai-ccai')
    location = "global"
    ds_id = "underwriter-loss-runs"
    
    search_client = discoveryengine.SearchServiceClient()
    serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{ds_id}/servingConfigs/default_search"
    
    query = "Highest Paid claim cost dollar incident report cargo for acme"
    print(f"\nExecuting Query: '{query}'")
    
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=10,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True,
                max_snippet_count=5
            )
        )
    )
    
    try:
        response = search_client.search(request)
        snippets = []
        print("\n--- Vertex AI Search Raw Response Objects ---")
        for i, result in enumerate(response.results):
            if result.document.id != client_name:
                continue
            
            print(f"\nResult {i+1}: Document ID = {result.document.id}")
            if result.document.derived_struct_data:
                # Prioritize high-quality extractive segments if available
                extractive_segments = result.document.derived_struct_data.get("extractive_segments", [])
                for segment in extractive_segments:
                    snippets.append(segment.get("content", ""))
                    print(f"  [Extracted Segment]: {segment.get('content')}")
                # Fallback to standard contextual snippets
                snippets_list = result.document.derived_struct_data.get("snippets", [])
                for snip in snippets_list:
                    snippets.append(snip.get("snippet", ""))
                    print(f"  [Snippet]: {snip.get('snippet')}")

        if not snippets:
            print(f"\n⚠️  No relevant claims history or snippets found for client '{client_name}'. The index may still be building.")
            return
            
        print("\n==========================================")
        print("FINAL CONTEXT STRING FED TO GEMINI:\n")
        print(" \n...\n ".join(snippets))
        print("==========================================")
        
    except Exception as e:
        print(f"\n❌ Vertex AI Search execution failed: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script to inspect RAG query snippets.")
    parser.add_argument("--client", type=str, default="stella", help="The client ID to query (e.g. acme, zenith, stella)")
    args = parser.parse_args()
    
    query_datastore(args.client)
