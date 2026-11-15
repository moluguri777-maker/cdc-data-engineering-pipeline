
import json
from datetime import datetime

import pytest

from src.database.repository import DatabaseRepository


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.executed_queries = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed_queries.append((query, params))

    def fetchone(self):
        return self.connection.fetchone_result

    @property
    def rowcount(self):
        return self.connection.rowcount

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.fetchone_result = None
        self.rowcount = 1
        self.cursors = []
        self.closed = False

    def cursor(self, dictionary=False):
        cursor = FakeCursor(self)
        self.cursors.append(cursor)
        return cursor

    def is_connected(self):
        return not self.closed

    def close(self):
        self.closed = True


@pytest.fixture
def setup_repository():
    connection = FakeConnection()
    repository = DatabaseRepository(connection=connection)
    return repository, connection


def create_event():
    return {
        "event_id": "EVT001",
        "customer_id": "CUST001",
        "operation": "INSERT",
        "source_version": 1,
        "event_timestamp": "2026-11-15T10:00:00",
        "data": {
            "customer_name": "Test Customer",
            "email": "test@example.com",
            "city": "Hyderabad",
        },
    }


def test_repository_accepts_injected_connection(setup_repository):
    repository, connection = setup_repository

    assert repository.connection is connection


def test_create_pipeline_run_executes_insert(setup_repository):
    repository, connection = setup_repository

    repository.create_pipeline_run("RUN001")

    query, params = connection.cursors[0].executed_queries[0]

    assert "INSERT INTO pipeline_runs" in query
    assert params[0] == "RUN001"
    assert isinstance(params[1], datetime)


def test_get_customer_returns_database_record(setup_repository):
    repository, connection = setup_repository

    expected = {
        "customer_id": "CUST001",
        "customer_name": "Test Customer",
    }
    connection.fetchone_result = expected

    result = repository.get_customer("CUST001")

    assert result == expected
    query, params = connection.cursors[0].executed_queries[0]
    assert "FROM customers_current" in query
    assert params == ("CUST001",)


def test_is_event_processed_returns_true(setup_repository):
    repository, connection = setup_repository
    connection.fetchone_result = ("EVT001",)

    assert repository.is_event_processed("EVT001") is True


def test_is_event_processed_returns_false(setup_repository):
    repository, connection = setup_repository
    connection.fetchone_result = None

    assert repository.is_event_processed("EVT001") is False


def test_save_event_history_executes_insert(setup_repository):
    repository, connection = setup_repository
    event = create_event()

    repository.save_event_history(event, "RUN001")

    query, params = connection.cursors[0].executed_queries[0]

    assert "INSERT INTO customer_event_history" in query
    assert params[0] == "EVT001"
    assert params[1] == "CUST001"
    assert params[2] == "INSERT"
    assert params[3] == 1
    assert isinstance(params[7], datetime)
    assert params[8] == "RUN001"


def test_upsert_customer_executes_insert_or_update(setup_repository):
    repository, connection = setup_repository
    event = create_event()

    repository.upsert_customer(event)

    query, params = connection.cursors[0].executed_queries[0]

    assert "INSERT INTO customers_current" in query
    assert "ON DUPLICATE KEY UPDATE" in query
    assert params[0] == "CUST001"
    assert params[1] == "Test Customer"
    assert params[4] == 1


def test_mark_customer_deleted_returns_rowcount(setup_repository):
    repository, connection = setup_repository
    connection.rowcount = 1

    event = create_event()
    event["operation"] = "DELETE"
    event["data"] = {}

    result = repository.mark_customer_deleted(event)

    query, params = connection.cursors[0].executed_queries[0]

    assert "UPDATE customers_current" in query
    assert "is_deleted = TRUE" in query
    assert result == 1
    assert params[0] == 1
    assert params[1] == "EVT001"
    assert params[3] == "CUST001"


def test_save_processed_event_executes_insert(setup_repository):
    repository, connection = setup_repository
    event = create_event()

    repository.save_processed_event(event, "RUN001", "PROCESSED")

    query, params = connection.cursors[0].executed_queries[0]

    assert "INSERT INTO processed_events" in query
    assert params == (
        "EVT001",
        "CUST001",
        1,
        "RUN001",
        "PROCESSED",
    )


def test_save_rejected_event_inserts_new_rejection(setup_repository):
    repository, connection = setup_repository
    event = create_event()

    result = repository.save_rejected_event(
        event,
        "RUN001",
        "Invalid event",
    )

    assert result is True
    assert len(connection.cursors[0].executed_queries) == 2

    insert_query, params = connection.cursors[0].executed_queries[1]

    assert "INSERT INTO rejected_events" in insert_query
    assert params[0] == "EVT001"
    assert params[1] == "CUST001"
    assert params[2] == "RUN001"
    assert params[3] == "Invalid event"
    assert json.loads(params[4]) == event


def test_save_rejected_event_skips_existing_rejection(setup_repository):
    repository, connection = setup_repository
    event = create_event()

    connection.fetchone_result = (1,)

    result = repository.save_rejected_event(
        event,
        "RUN002",
        "Invalid event",
    )

    assert result is False
    assert len(connection.cursors[0].executed_queries) == 1


def test_finish_pipeline_run_executes_update(setup_repository):
    repository, connection = setup_repository

    repository.finish_pipeline_run(
        run_id="RUN001",
        status="SUCCESS",
        total_events=10,
        accepted_events=8,
        rejected_events=1,
        duplicate_events=1,
    )

    query, params = connection.cursors[0].executed_queries[0]

    assert "UPDATE pipeline_runs" in query
    assert params[1] == "SUCCESS"
    assert params[2:6] == (10, 8, 1, 1)
    assert params[7] == "RUN001"
    assert isinstance(params[0], datetime)


def test_get_event_by_customer_version_returns_record(setup_repository):
    repository, connection = setup_repository
    expected = {"event_id": "EVT001", "operation": "INSERT"}
    connection.fetchone_result = expected

    result = repository.get_event_by_customer_version("CUST001", 1)

    assert result == expected
    query, params = connection.cursors[0].executed_queries[0]

    assert "FROM customer_event_history" in query
    assert params == ("CUST001", 1)


def test_create_tombstone_inserts_deleted_customer(setup_repository):
    repository, connection = setup_repository
    event = create_event()
    event["operation"] = "DELETE"
    event["data"] = {}

    repository.create_tombstone(event)

    query, params = connection.cursors[0].executed_queries[0]

    assert "INSERT INTO customers_current" in query
    assert "VALUES (%s, NULL, NULL, NULL, %s, TRUE" in query
    assert params[0] == "CUST001"
    assert params[1] == 1
    assert params[2] == "EVT001"
    assert isinstance(params[3], datetime)


def test_close_closes_database_connection(setup_repository):
    repository, connection = setup_repository

    repository.close()

    assert connection.closed is True


def test_close_does_not_close_already_closed_connection(setup_repository):
    repository, connection = setup_repository
    connection.closed = True

    repository.close()

    assert connection.closed is True
