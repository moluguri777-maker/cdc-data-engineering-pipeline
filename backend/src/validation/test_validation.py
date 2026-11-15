
import pytest

from src.validation.validation_service import validate_events


def create_valid_event():
    return {
        "event_id": "TEST001",
        "customer_id": "CUST001",
        "operation": "INSERT",
        "source_version": 1,
        "event_timestamp": "2026-11-15T10:00:00",
        "data": {
            "customer_name": "Test Customer",
            "email": "test@example.com",
            "city": "Hyderabad"
        }
    }


def test_valid_event_is_accepted():
    event = create_valid_event()

    accepted, rejected = validate_events([event])

    assert len(accepted) == 1
    assert len(rejected) == 0


def test_non_dictionary_event_is_rejected():
    accepted, rejected = validate_events(["invalid"])

    assert len(accepted) == 0
    assert rejected[0]["reason"] == "Event must be a JSON object"


def test_missing_required_field_is_rejected():
    event = create_valid_event()
    del event["customer_id"]

    accepted, rejected = validate_events([event])

    assert len(accepted) == 0
    assert "Missing fields" in rejected[0]["reason"]


def test_empty_customer_id_is_rejected():
    event = create_valid_event()
    event["customer_id"] = ""

    accepted, rejected = validate_events([event])

    assert len(accepted) == 0
    assert rejected[0]["reason"] == "Invalid customer_id"


def test_unsupported_operation_is_rejected():
    event = create_valid_event()
    event["operation"] = "UPSERT"

    accepted, rejected = validate_events([event])

    assert len(accepted) == 0
    assert rejected[0]["reason"] == "Unsupported operation"


@pytest.mark.parametrize("version", [0, -1, True, "1"])
def test_invalid_source_version_is_rejected(version):
    event = create_valid_event()
    event["source_version"] = version

    accepted, rejected = validate_events([event])

    assert len(accepted) == 0
    assert "source_version" in rejected[0]["reason"]


def test_invalid_timestamp_is_rejected():
    event = create_valid_event()
    event["event_timestamp"] = "not-a-timestamp"

    accepted, rejected = validate_events([event])

    assert len(accepted) == 0
    assert rejected[0]["reason"] == "Invalid event_timestamp"


def test_data_must_be_dictionary():
    event = create_valid_event()
    event["data"] = "invalid data"

    accepted, rejected = validate_events([event])

    assert len(accepted) == 0
    assert rejected[0]["reason"] == "data must be a JSON object"


def test_empty_customer_name_is_rejected():
    event = create_valid_event()
    event["data"]["customer_name"] = ""

    accepted, rejected = validate_events([event])

    assert len(accepted) == 0
    assert rejected[0]["reason"] == (
        "Customer attributes must be non-empty strings"
    )


def test_exact_duplicate_event_is_rejected():
    event = create_valid_event()

    accepted, rejected = validate_events([event, event.copy()])

    assert len(accepted) == 1
    assert len(rejected) == 1
    assert rejected[0]["reason"] == "Exact duplicate event"


def test_conflicting_event_id_is_rejected():
    event1 = create_valid_event()
    event2 = create_valid_event()

    event2["data"]["customer_name"] = "Different Customer"

    accepted, rejected = validate_events([event1, event2])

    assert len(accepted) == 1
    assert len(rejected) == 1
    assert rejected[0]["reason"] == (
        "Conflicting event with same event_id"
    )


def test_delete_event_with_empty_data_is_accepted():
    event = create_valid_event()
    event["operation"] = "DELETE"
    event["data"] = {}

    accepted, rejected = validate_events([event])

    assert len(accepted) == 1
    assert len(rejected) == 0
