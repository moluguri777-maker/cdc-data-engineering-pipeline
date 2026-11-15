
from datetime import datetime
import json


VALID_OPERATIONS = {"INSERT", "UPDATE", "DELETE"}

REQUIRED_FIELDS = {
    "event_id",
    "customer_id",
    "operation",
    "source_version",
    "event_timestamp",
    "data"
}


def validate_events(events):
    accepted_events = []
    rejected_events = []
    seen_events = {}

    for event in events:

        # 1. Event must be a dictionary
        if not isinstance(event, dict):
            rejected_events.append({
                "event": event,
                "reason": "Event must be a JSON object"
            })
            continue

        # 2. Check required fields
        missing_fields = REQUIRED_FIELDS - event.keys()

        if missing_fields:
            rejected_events.append({
                "event": event,
                "reason": f"Missing fields: {', '.join(sorted(missing_fields))}"
            })
            continue

        event_id = event["event_id"]

        # 3. Validate event ID
        if not isinstance(event_id, str) or not event_id.strip():
            rejected_events.append({
                "event": event,
                "reason": "Invalid event_id"
            })
            continue

        # 4. Detect duplicate event IDs
        if event_id in seen_events:
            if event == seen_events[event_id]:
                rejected_events.append({
                    "event": event,
                    "reason": "Exact duplicate event"
                })
            else:
                rejected_events.append({
                    "event": event,
                    "reason": "Conflicting event with same event_id"
                })
            continue

        # 5. Validate customer ID
        customer_id = event["customer_id"]

        if not isinstance(customer_id, str) or not customer_id.strip():
            rejected_events.append({
                "event": event,
                "reason": "Invalid customer_id"
            })
            continue

        # 6. Validate operation
        if event["operation"] not in VALID_OPERATIONS:
            rejected_events.append({
                "event": event,
                "reason": "Unsupported operation"
            })
            continue

        # 7. Validate source version
        version = event["source_version"]

        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            rejected_events.append({
                "event": event,
                "reason": "source_version must be a positive integer"
            })
            continue

        # 8. Validate timestamp
        try:
            datetime.fromisoformat(event["event_timestamp"])
        except (ValueError, TypeError):
            rejected_events.append({
                "event": event,
                "reason": "Invalid event_timestamp"
            })
            continue

        # 9. Validate data object
        if not isinstance(event["data"], dict):
            rejected_events.append({
                "event": event,
                "reason": "data must be a JSON object"
            })
            continue

        # 10. Validate customer attributes
        if event["operation"] in {"INSERT", "UPDATE"}:
            data = event["data"]

            required_customer_fields = {
                "customer_name",
                "email",
                "city"
            }

            missing_customer_fields = (
                required_customer_fields - data.keys()
            )

            if missing_customer_fields:
                rejected_events.append({
                    "event": event,
                    "reason": (
                        "Missing customer fields: "
                        + ", ".join(sorted(missing_customer_fields))
                    )
                })
                continue

            if not all(
                isinstance(data[field], str) and data[field].strip()
                for field in required_customer_fields
            ):
                rejected_events.append({
                    "event": event,
                    "reason": "Customer attributes must be non-empty strings"
                })
                continue

        # Event passed validation
        accepted_events.append(event)
        seen_events[event_id] = event

    return accepted_events, rejected_events
