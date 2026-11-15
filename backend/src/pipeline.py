
import logging
import uuid
from pathlib import Path
from datetime import datetime

from src.ingestion.ingestion_service import ingest_events
from src.validation.validation_service import validate_events
from src.database.repository import DatabaseRepository
from src.transformation.cdc_processor import CDCProcessor


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = BASE_DIR / "data" / "incoming" / "customer_events.json"


def run_pipeline(file_path):
    repository = DatabaseRepository()

    run_id = (
        f"RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}-"
        f"{uuid.uuid4().hex[:8]}"
    )

    total_events = 0
    accepted_events = 0
    rejected_events = 0
    duplicate_events = 0
    error_message = None
    status = "FAILED"

    logger.info("Starting pipeline run: %s", run_id)

    try:
        # 1. Create the pipeline run before inserting related records.
        repository.create_pipeline_run(run_id)
        repository.connection.commit()

        # 2. Ingest events from the JSON file.
        events = ingest_events(file_path)
        total_events = len(events)

        logger.info("Total events received: %s", total_events)

        # 3. Validate incoming events.
        valid_events, invalid_events = validate_events(events)

        logger.info("Valid events: %s", len(valid_events))
        logger.info("Invalid events: %s", len(invalid_events))

        # 4. Persist validation failures.
        for item in invalid_events:
            repository.connection.start_transaction()

            repository.save_rejected_event(
                item["event"],
                run_id,
                item["reason"]
            )

            repository.connection.commit()

            reason = item["reason"].lower()

            if "duplicate" in reason:
                duplicate_events += 1
            else:
                rejected_events += 1

        # 5. Process valid events through the CDC processor.
        processor = CDCProcessor(repository)
        results = processor.process_events(valid_events, run_id)

        logger.info("CDC processing results: %s", results)

        accepted_events = (
            results["PROCESSED"] + results["STALE"]
        )

        duplicate_events += results["DUPLICATE"]
        rejected_events += results["REJECTED"] + results["FAILED"]

        # 6. Determine the final pipeline status.
        if results["FAILED"] > 0:
            status = "PARTIAL_SUCCESS" if accepted_events > 0 else "FAILED"
        elif rejected_events > 0 or duplicate_events > 0:
            status = "PARTIAL_SUCCESS"
        else:
            status = "SUCCESS"

    except Exception as error:
        error_message = str(error)
        status = "FAILED"

        logger.exception("Pipeline execution failed")

    finally:
        # 7. Update pipeline execution metrics.
        try:
            cursor = repository.connection.cursor()

            cursor.execute(
                """
                UPDATE pipeline_runs
                SET end_time = %s,
                    status = %s,
                    total_events = %s,
                    accepted_events = %s,
                    rejected_events = %s,
                    duplicate_events = %s,
                    error_message = %s
                WHERE run_id = %s
                """,
                (
                    datetime.now(),
                    status,
                    total_events,
                    accepted_events,
                    rejected_events,
                    duplicate_events,
                    error_message,
                    run_id
                )
            )

            repository.connection.commit()
            cursor.close()

        except Exception:
            repository.connection.rollback()
            logger.exception("Could not update pipeline run metrics")

        repository.close()

        logger.info("Pipeline run completed: %s", run_id)
        logger.info("Final status: %s", status)
        logger.info("Total events: %s", total_events)
        logger.info("Accepted events: %s", accepted_events)
        logger.info("Rejected events: %s", rejected_events)
        logger.info("Duplicate events: %s", duplicate_events)

    return run_id


if __name__ == "__main__":
    run_pipeline(INPUT_FILE)
