"""
Demo batch script — fires 15-20 weigh+print cycles through the real API
to generate a realistic set of box records for testing/演示.

Usage:
    python demo_batch.py <station_id> [count]

Example:
    python demo_batch.py 1        # fires 15-20 boxes on station 1
    python demo_batch.py 2 25     # fires exactly 25 boxes on station 2

Prerequisites:
    1. Start the backend:  cd backend && venv\Scripts\activate && python -m uvicorn app.main:app --reload
    2. Start the mock scale: python test_harness\mock_scale_server.py 5005 12.180
    3. Start the mock printer: python test_harness\mock_printer_server.py 9100
"""
import sys
import requests
import time
import random
from datetime import datetime

API_BASE = "http://localhost:8000"


def run_batch(station_id: int, count: int = 0) -> None:
    if count <= 0:
        count = random.randint(15, 20)

    print(f"\n{'='*50}")
    print(f" DEMO BATCH: {count} boxes on Station {station_id}")
    print(f" {'='*50}\n")

    for i in range(count):
        try:
            resp = requests.post(
                f"{API_BASE}/api/stations/{station_id}/weigh",
                json={"station_id": station_id, "batch_number": "", "operator": ""},
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"  [{i+1:02d}/{count}] ✓ {data['box_id']} | {data['weight']} kg | {data['print_status']}")
            else:
                error = resp.json().get("detail", resp.text)
                print(f"  [{i+1:02d}/{count}] ✗ HTTP {resp.status_code}: {error}")
        except requests.exceptions.ConnectionError:
            print(f"  [{i+1:02d}/{count}] ✗ Connection failed — is the backend running?")
            break
        except Exception as e:
            print(f"  [{i+1:02d}/{count}] ✗ Unexpected error: {e}")

        # Slight delay between boxes, with random variance
        time.sleep(random.uniform(0.3, 0.7))

    print(f"\n{'='*50}")
    print(f" Batch complete: {count} boxes processed")
    print(f" {'='*50}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    try:
        station_id = int(sys.argv[1])
    except ValueError:
        print("Station ID must be an integer.")
        sys.exit(1)

    count = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    # Verify station exists
    try:
        resp = requests.get(f"{API_BASE}/api/stations/{station_id}")
        if resp.status_code != 200:
            print(f"Station {station_id} not found.")
            sys.exit(1)
        station = resp.json()
        print(f"Using station: {station['name']} ({station['machine_id']})")
    except requests.exceptions.ConnectionError:
        print("Cannot reach the API. Start the backend first.")
        sys.exit(1)

    run_batch(station_id, count)