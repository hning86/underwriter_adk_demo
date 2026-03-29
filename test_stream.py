import os
import asyncio
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from backend.underwriter_agent.agent import app as agent_app

async def main():
    runner = Runner(
        app=agent_app,
        session_service=InMemorySessionService(),
        auto_create_session=True
    )
    
    prompt = "Provide a risk assessment summary for client profile: acme"
    print("Starting stream...")
    
    async for event in runner.run_async(
        user_id="test_ui",
        session_id="test_session_acme",
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)])
    ):
        print("\n--- NEW EVENT ---")
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"TEXT CHUNK: {part.text}")
                elif getattr(part, "function_call", None):
                    print(f"FUNCTION CALL: {part.function_call.name} (args: {part.function_call.args})")
                elif getattr(part, "function_response", None):
                    print(f"FUNCTION RESPONSE: {part.function_response.name} ")
                    # print(f"Response data: {part.function_response.response}")
                else:
                    print(f"OTHER PART: {part}")

if __name__ == "__main__":
    asyncio.run(main())
