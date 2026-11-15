
import json
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "incoming"


def generate_events(customer_count=25, seed=42):
    rng = random.Random(seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    events = []
    version_tracker = defaultdict(int)

    start_time = datetime(2026, 11, 15, 10, 0, 0)

    cities = ["Hyderabad", "Bangalore", "Chennai", "Mumbai"]

    # Generate valid customer lifecycles
    for customer_num in range(1, customer_count + 1):
        customer_id = f"CUST{customer_num:04d}"

        operations = ["INSERT", "UPDATE", "UPDATE"]

        # Some customers will also have a DELETE event
        if customer_num % 5 == 0:
            operations.append("DELETE")

        customer_name = f"Customer {customer_num}"
        email = f"customer{customer_num}@example.com"
        city = rng.choice(cities)

        for operation in operations:
            version_tracker[customer_id] += 1
            version = version_tracker[customer_id]

            if operation == "UPDATE":
                city = rng.choice(cities)

            event = {
                "event_id": f"EVT{len(events) + 1:06d}",
                "customer_id": customer_id,
                "operation": operation,
                "source_version": version,
                "event_timestamp": (
                    start_time + timedelta(seconds=len(events) + 1)
                ).isoformat(),
                "data": {
                    "customer_name": customer_name,
                    "email": email,
                    "city": city
                }
            }

            events.append(event)

    # Exact duplicate
    duplicate = events[1].copy()
    events.append(duplicate)

    # Invalid operation
    events.append({
        "event_id": "EVT_INVALID_001",
        "customer_id": "CUST0001",
        "operation": "UPSERT",
        "source_version": 99,
        "event_timestamp": start_time.isoformat(),
        "data": {}
    })

    # Missing customer_id
    events.append({
        "event_id": "EVT_INVALID_002",
        "operation": "INSERT",
        "source_version": 100,
        "event_timestamp": start_time.isoformat(),
        "data": {}
    })

    # Out-of-order arrival
    rng.shuffle(events)

    output_file = OUTPUT_DIR / "customer_events.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=4)

    print("CDC dataset generated successfully!")
    print(f"Customers: {customer_count}")
    print(f"Total events: {len(events)}")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--customers", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    if args.customers < 1:
        parser.error("--customers must be at least 1")

    generate_events(args.customers, args.seed)
