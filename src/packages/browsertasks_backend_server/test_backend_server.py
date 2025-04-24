import requests
import time

API_URL = "http://localhost:8888"

def test_run_task(task, headless=True):
    resp = requests.post(f"{API_URL}/run", json={"task": task}, params={"headless": headless})
    print("POST /run response:", resp.status_code, resp.json())

# def test_run_stream(task, headless=False):
#     import sseclient
#     resp = requests.post(f"{API_URL}/run_stream", json={"task": task}, params={"headless": headless}, stream=True)
#     client = sseclient.SSEClient(resp)
#     print("Streaming output:")
#     for event in client.events():
#         print(event.data)
#         # Stop after first few chunks for demo
#         break

# def test_last_responses():
#     resp = requests.get(f"{API_URL}/lastResponses")
#     print("GET /lastResponses:", resp.status_code, resp.json())

if __name__ == "__main__":
    # Example usage
    test_run_task("Go to google.com and search for OLAS", headless=True)
    time.sleep(2)
    # test_last_responses()
    # Uncomment to test streaming (requires sseclient-py)
    # test_run_stream("Go to google.com and search for OLAS", headless=True)
