import requests
import uuid
import json

BASE_URL = "http://127.0.0.1:8000"
STREAM_ENDPOINT = "/agents/query/stream"

# Generate a single conversation ID for the entire test run
conversation_id = str(uuid.uuid4())

def run_test(test_name, question):
    """Runs a single test case against the streaming endpoint."""
    print(f"\n--- Running Test: {test_name} ---")
    print(f"Question: {question}")
    
    payload = {
        "question": question,
        "conversation_id": conversation_id  # Use the same ID for all tests
    }
    
    full_response = ""
    try:
        with requests.post(f"{BASE_URL}{STREAM_ENDPOINT}", json=payload, stream=True) as response:
            response.raise_for_status()
            # The response is now plain text, not SSE with JSON
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                full_response += chunk

    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        full_response = f"Error: Could not connect to the agent."

    print(f"Response:\n{full_response}")
    print("--- Test Complete ---")

if __name__ == "__main__":
    # Test 1: Simple procurement question
    run_test("Simple procurement question", "What is the policy for buying a new laptop?")

    # Test 2: Follow-up question to test conversation history
    run_test("Follow-up question to test conversation history", "What is the spending limit for that?")

    # Test 3: Off-topic question to test guards
    run_test("Off-topic question to test guards", "What's the weather like in Seattle?")

URL = "http://127.0.0.1:8000/agents/query/stream"

# Test scenarios
TEST_QUERIES = [
    {
        "description": "Simple procurement question",
        "payload": {
            "question": "What is the policy for buying a new laptop?",
            "conversation_id": "test-convo-1"
        }
    },
    {
        "description": "Follow-up question to test conversation history",
        "payload": {
            "question": "What is the spending limit for that?",
            "conversation_id": "test-convo-1"  # Same ID to maintain context
        }
    },
    {
        "description": "Off-topic question to test guards",
        "payload": {
            "question": "What's the weather like in Seattle?",
            "conversation_id": "test-convo-2"
        }
    }
]

def run_test(description, payload):
    """Sends a request to the streaming endpoint and prints the response."""
    print(f"\n--- Running Test: {description} ---")
    print(f"Question: {payload['question']}")
    print("Response:")
    full_response = ""
    
    try:
        with requests.post(URL, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()  # Raise an exception for bad status codes
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data:'):
                        # The server now sends plain text, so just print the data part.
                        print(decoded_line[len('data:'):].strip(), end="")

    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Request failed: {e}")
    
    print("\n--- Test Complete ---\n")

if __name__ == "__main__":
    for test in TEST_QUERIES:
        run_test(test["description"], test["payload"])
