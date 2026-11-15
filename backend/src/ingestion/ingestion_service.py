
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ingest_events(file_path):
    """
    Read CDC events from a JSON file.

    Returns:
        list: Loaded event records.
    """

    path = Path(file_path)

    # 1. Check whether file exists
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}"
        )

    # 2. Check whether file is empty
    if path.stat().st_size == 0:
        logger.warning("Input file is empty.")
        return []

    # 3. Read and parse JSON
    try:
        with open(path, "r", encoding="utf-8") as file:
            events = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Malformed JSON file: {error}"
        ) from error

    # 4. Validate top-level structure
    if not isinstance(events, list):
        raise ValueError(
            "Expected a JSON array containing events."
        )

    logger.info(
        "Successfully ingested %d events from %s",
        len(events),
        path.name
    )

    return events
