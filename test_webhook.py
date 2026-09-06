import threading
import time
import requests
import webhook_server

def run_test():
    # Start Webhook Server in a background daemon thread
    server_thread = threading.Thread(target=webhook_server.run_server, kwargs={"port": 5005}, daemon=True)
    server_thread.start()
    time.sleep(1)

    url = "http://127.0.0.1:5005/"
    
    # 1. Test GET healthcheck
    resp_get = requests.get(url)
    print(f"GET Response Status: {resp_get.status_code}")
    print(f"GET Content: {resp_get.json()}\n")
    assert resp_get.status_code == 200

    # 2. Test POST Webhook Payload (Simulating incoming Discord/custom webhook)
    payload = {
        "message": "Check out this product on Blinkit - Hot Wheels Chop N Bloc Die Cast Car\nhttps://blinkit.com/prn/x/prid/787541"
    }
    
    print("Sending POST Webhook Payload...")
    resp_post = requests.post(url, json=payload)
    print(f"POST Response Status: {resp_post.status_code}")
    print(f"POST Response Data:\n{resp_post.text}\n")
    assert resp_post.status_code == 200
    assert resp_post.json()["status"] == "success"
    assert resp_post.json()["product_id"] == "787541"

    print("✅ Webhook Server integration test passed successfully!")

if __name__ == "__main__":
    run_test()
