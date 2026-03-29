import os
import sys
import argparse

# Bootstrap the Python path to correctly resolve the sibling 'backend' module natively
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.underwriter_agent.tools import get_loss_run_report

def query_datastore(client_name: str):
    print(f"\n🚀 Directly Invoking RAG Ensemble for Client: '{client_name.upper()}'\n")
    
    try:
        response = get_loss_run_report(client_name)
        if "error" in response:
            print(f"\n❌ Execution Error:\n{response['error']}")
        else:
            print("\n✅ Final JSON Payload Returned to Agent:")
            print(response)
    except Exception as e:
        print(f"\n❌ Exception caught during execution: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script to inspect RAG query snippets.")
    parser.add_argument("--client", type=str, default="stella", help="The client ID to query (e.g. acme, zenith, stella)")
    args = parser.parse_args()
    
    query_datastore(args.client)
