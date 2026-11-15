
import json
import pytest

from src.ingestion.ingestion_service import ingest_events


def test_valid_json_file_is_ingested(tmp_path):
    events = [
        {
            "event_id": "TEST001",
            "customer_id": "CUST001",
            "operation": "INSERT"
        }
    ]

    file_path = tmp_path / "valid_events.json"
    file_path.write_text(json.dumps(events), encoding="utf-8")

    result = ingest_events(file_path)

    assert result == events
    assert len(result) == 1


def test_empty_file_returns_empty_list(tmp_path):
    file_path = tmp_path / "empty.json"
    file_path.write_text("", encoding="utf-8")

    result = ingest_events(file_path)

    assert result == []


def test_missing_file_raises_error(tmp_path):
    file_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        ingest_events(file_path)


def test_malformed_json_raises_value_error(tmp_path):
    file_path = tmp_path / "malformed.json"
    file_path.write_text(
        '[{"event_id": "TEST001",}]',
        encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Malformed JSON file"):
        ingest_events(file_path)


def test_json_object_instead_of_array_is_rejected(tmp_path):
    file_path = tmp_path / "invalid_structure.json"
    file_path.write_text(
        json.dumps({"event_id": "TEST001"}),
        encoding="utf-8"
    )

    with pytest.raises(
        ValueError,
        match="Expected a JSON array"
    ):
        ingest_events(file_path)
