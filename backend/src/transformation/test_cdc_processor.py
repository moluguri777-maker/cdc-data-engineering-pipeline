
import pytest

from src.transformation.cdc_processor import CDCProcessor


class FakeConnection:
    """Simulates database transaction operations."""

    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def start_transaction(self):
        pass

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class FakeRepository:
    """In-memory repository: no real MySQL database is used."""

    def __init__(self):
        self.connection = FakeConnection()
        self.customers = {}
        self.processed_events = set()
        self.history = {}
        self.rejected_events = []

    def is_event_processed(self, event_id):
        return event_id in self.processed_events

    def get_customer(self, customer_id):
        return self.customers.get(customer_id)

    def get_event_by_customer_version(self, customer_id, version):
        return self.history.get((customer_id, version))

    def upsert_customer(self, event):
        customer_id = event["customer_id"]
        self.customers[customer_id] = {
            **event["data"],
            "source_version": event["source_version"],
            "is_deleted": False,
            "last_event_id": event["event_id"],
        }

    def mark_customer_deleted(self, event):
        customer = self.customers[event["customer_id"]]
        customer["source_version"] = event["source_version"]
        customer["is_deleted"] = True
        customer["last_event_id"] = event["event_id"]

    def create_tombstone(self, event):
        self.customers[event["customer_id"]] = {
            "customer_name": None,
            "email": None,
            "city": None,
            "source_version": event["source_version"],
            "is_deleted": True,
            "last_event_id": event["event_id"],
        }

    def save_event_history(self, event, run_id):
        key = (event["customer_id"], event["source_version"])
        self.history[key] = event.copy()

    def save_processed_event(self, event, run_id, status):
        self.processed_events.add(event["event_id"])

    def save_rejected_event(self, event, run_id, reason):
        self.rejected_events.append({
            "event": event,
            "reason": reason,
        })


def create_event(
    event_id="EVT001",
    customer_id="CUST001",
    operation="INSERT",
    version=1,
    name="Test Customer",
):
    return {
        "event_id": event_id,
        "customer_id": customer_id,
        "operation": operation,
        "source_version": version,
        "event_timestamp": "2026-11-15T10:00:00",
        "data": {
            "customer_name": name,
            "email": "test@example.com",
            "city": "Hyderabad",
        } if operation != "DELETE" else {},
    }


@pytest.fixture
def setup_processor():
    repository = FakeRepository()
    processor = CDCProcessor(repository)
    return processor, repository


def test_insert_creates_customer(setup_processor):
    processor, repository = setup_processor
    event = create_event()

    result = processor.process_event(event, "RUN001")

    assert result == "PROCESSED"
    assert repository.customers["CUST001"]["customer_name"] == "Test Customer"
    assert repository.customers["CUST001"]["source_version"] == 1
    assert ("CUST001", 1) in repository.history
    assert "EVT001" in repository.processed_events


def test_update_changes_customer_details(setup_processor):
    processor, repository = setup_processor

    insert_event = create_event()
    processor.process_event(insert_event, "RUN001")

    update_event = create_event(
        event_id="EVT002",
        operation="UPDATE",
        version=2,
        name="Updated Customer",
    )

    result = processor.process_event(update_event, "RUN001")

    assert result == "PROCESSED"
    assert repository.customers["CUST001"]["customer_name"] == "Updated Customer"
    assert repository.customers["CUST001"]["source_version"] == 2


def test_delete_marks_customer_as_deleted(setup_processor):
    processor, repository = setup_processor

    processor.process_event(create_event(), "RUN001")

    delete_event = create_event(
        event_id="EVT002",
        operation="DELETE",
        version=2,
    )

    result = processor.process_event(delete_event, "RUN001")

    assert result == "PROCESSED"
    assert repository.customers["CUST001"]["is_deleted"] is True
    assert repository.customers["CUST001"]["source_version"] == 2


def test_duplicate_event_is_not_processed_twice(setup_processor):
    processor, repository = setup_processor
    event = create_event()

    first_result = processor.process_event(event, "RUN001")
    second_result = processor.process_event(event, "RUN002")

    assert first_result == "PROCESSED"
    assert second_result == "DUPLICATE"
    assert len(repository.history) == 1


def test_stale_event_does_not_overwrite_newer_customer(setup_processor):
    processor, repository = setup_processor

    newer_event = create_event(
        event_id="EVT003",
        version=3,
        name="Latest Customer",
    )
    processor.process_event(newer_event, "RUN001")

    stale_event = create_event(
        event_id="EVT001",
        version=1,
        name="Old Customer",
    )

    result = processor.process_event(stale_event, "RUN001")

    assert result == "STALE"
    assert repository.customers["CUST001"]["customer_name"] == "Latest Customer"
    assert repository.customers["CUST001"]["source_version"] == 3
    assert ("CUST001", 1) in repository.history


def test_out_of_order_events_preserve_latest_version(setup_processor):
    processor, repository = setup_processor

    events = [
        create_event("EVT003", version=3, name="Version 3"),
        create_event("EVT001", version=1, name="Version 1"),
        create_event("EVT002", version=2, name="Version 2"),
    ]

    results = [
        processor.process_event(event, "RUN001")
        for event in events
    ]

    customer = repository.customers["CUST001"]

    assert results == ["PROCESSED", "STALE", "STALE"]
    assert customer["customer_name"] == "Version 3"
    assert customer["source_version"] == 3
    assert len(repository.history) == 3


def test_delete_before_insert_creates_tombstone(setup_processor):
    processor, repository = setup_processor

    delete_event = create_event(
        event_id="EVT002",
        operation="DELETE",
        version=2,
    )

    result = processor.process_event(delete_event, "RUN001")

    customer = repository.customers["CUST001"]

    assert result == "PROCESSED"
    assert customer["is_deleted"] is True
    assert customer["source_version"] == 2
    assert customer["customer_name"] is None


def test_conflicting_customer_version_is_rejected(setup_processor):
    processor, repository = setup_processor

    first_event = create_event()
    processor.process_event(first_event, "RUN001")

    conflicting_event = create_event(
        event_id="EVT999",
        version=1,
        name="Different Customer",
    )

    result = processor.process_event(conflicting_event, "RUN001")

    assert result == "REJECTED"
    assert len(repository.rejected_events) == 1
    assert repository.rejected_events[0]["reason"] == (
        "Conflicting event: customer version already exists"
    )
