
import json
from datetime import datetime

from config.database import get_db_connection


class DatabaseRepository:
    """
    Handles all database operations for the CDC pipeline.

    Transaction commits and rollbacks are controlled by
    the caller (CDC processor / pipeline orchestrator).
    """

    def __init__(self, connection=None):
        self.connection = connection or get_db_connection()

    # 1. Pipeline run management

    def create_pipeline_run(self, run_id):
        query = """
            INSERT INTO pipeline_runs (
                run_id,
                start_time,
                status
            )
            VALUES (%s, %s, 'RUNNING')
        """

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                query,
                (run_id, datetime.now())
            )
        finally:
            cursor.close()

    # 2. Retrieve current customer state

    def get_customer(self, customer_id):
        query = """
            SELECT
                customer_id,
                customer_name,
                email,
                city,
                source_version,
                is_deleted,
                last_event_id,
                source_event_time
            FROM customers_current
            WHERE customer_id = %s
        """

        cursor = self.connection.cursor(dictionary=True)

        try:
            cursor.execute(query, (customer_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    # 3. Check whether event was processed

    def is_event_processed(self, event_id):
        query = """
            SELECT event_id
            FROM processed_events
            WHERE event_id = %s
        """

        cursor = self.connection.cursor()

        try:
            cursor.execute(query, (event_id,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # 4. Save accepted event history

    def save_event_history(self, event, run_id):
        data = event.get("data") or {}

        query = """
            INSERT INTO customer_event_history (
                event_id,
                customer_id,
                operation,
                source_version,
                customer_name,
                email,
                city,
                source_event_time,
                run_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                query,
                (
                    event["event_id"],
                    event["customer_id"],
                    event["operation"],
                    event["source_version"],
                    data.get("customer_name"),
                    data.get("email"),
                    data.get("city"),
                    datetime.fromisoformat(event["event_timestamp"]),
                    run_id
                )
            )
        finally:
            cursor.close()

    # 5. Insert or update current customer state

    def upsert_customer(self, event):
        data = event["data"]

        query = """
            INSERT INTO customers_current (
                customer_id,
                customer_name,
                email,
                city,
                source_version,
                is_deleted,
                last_event_id,
                source_event_time
            )
            VALUES (%s, %s, %s, %s, %s, FALSE, %s, %s)

            ON DUPLICATE KEY UPDATE
                customer_name = VALUES(customer_name),
                email = VALUES(email),
                city = VALUES(city),
                source_version = VALUES(source_version),
                is_deleted = FALSE,
                last_event_id = VALUES(last_event_id),
                source_event_time = VALUES(source_event_time)
        """

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                query,
                (
                    event["customer_id"],
                    data["customer_name"],
                    data["email"],
                    data["city"],
                    event["source_version"],
                    event["event_id"],
                    datetime.fromisoformat(event["event_timestamp"])
                )
            )
        finally:
            cursor.close()

    # 6. Mark customer as deleted

    def mark_customer_deleted(self, event):
        query = """
            UPDATE customers_current
            SET
                source_version = %s,
                is_deleted = TRUE,
                last_event_id = %s,
                source_event_time = %s
            WHERE customer_id = %s
        """

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                query,
                (
                    event["source_version"],
                    event["event_id"],
                    datetime.fromisoformat(event["event_timestamp"]),
                    event["customer_id"]
                )
            )

            return cursor.rowcount
        finally:
            cursor.close()

    # 7. Record processed or stale events

    def save_processed_event(self, event, run_id, status):
        query = """
            INSERT INTO processed_events (
                event_id,
                customer_id,
                source_version,
                run_id,
                processing_status
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                query,
                (
                    event["event_id"],
                    event["customer_id"],
                    event["source_version"],
                    run_id,
                    status
                )
            )
        finally:
            cursor.close()

    # 8. Save rejected events


    def save_rejected_event(self, event, run_id, reason):
        raw_event = json.dumps(event)
    
        # Check whether this exact event was already rejected.
        check_query = """
            SELECT rejection_id
            FROM rejected_events
            WHERE event_id <=> %s
              AND customer_id <=> %s
              AND rejection_reason = %s
              AND raw_event = CAST(%s AS JSON)
            LIMIT 1
        """
    
        cursor = self.connection.cursor()
    
        try:
            cursor.execute(
                check_query,
                (
                    event.get("event_id"),
                    event.get("customer_id"),
                    reason,
                    raw_event
                )
            )
    
            existing_record = cursor.fetchone()
    
            if existing_record:
                return False
    
            insert_query = """
                INSERT INTO rejected_events (
                    event_id,
                    customer_id,
                    run_id,
                    rejection_reason,
                    raw_event
                )
                VALUES (%s, %s, %s, %s, %s)
            """
    
            cursor.execute(
                insert_query,
                (
                    event.get("event_id"),
                    event.get("customer_id"),
                    run_id,
                    reason,
                    raw_event
                )
            )
    
            return True
    
        finally:
            cursor.close()


    # 9. Update pipeline execution metrics

    def finish_pipeline_run(
        self,
        run_id,
        status,
        total_events,
        accepted_events,
        rejected_events,
        duplicate_events,
        error_message=None
    ):
        query = """
            UPDATE pipeline_runs
            SET
                end_time = %s,
                status = %s,
                total_events = %s,
                accepted_events = %s,
                rejected_events = %s,
                duplicate_events = %s,
                error_message = %s
            WHERE run_id = %s
        """

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                query,
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
        finally:
            cursor.close()

    # 10. Close database connection 

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    
    # 11. Check whether a customer version already exists

    def get_event_by_customer_version(self, customer_id, source_version):
        query = """
            SELECT event_id, operation
            FROM customer_event_history
            WHERE customer_id = %s
              AND source_version = %s
        """

        cursor = self.connection.cursor(dictionary=True)

        try:
            cursor.execute(query, (customer_id, source_version))
            return cursor.fetchone()
        finally:
            cursor.close()

    # 12. Create a deletion tombstone

    def create_tombstone(self, event):
        query = """
            INSERT INTO customers_current (
                customer_id,
                customer_name,
                email,
                city,
                source_version,
                is_deleted,
                last_event_id,
                source_event_time
            )
            VALUES (%s, NULL, NULL, NULL, %s, TRUE, %s, %s)
        """

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                query,
                (
                    event["customer_id"],
                    event["source_version"],
                    event["event_id"],
                    datetime.fromisoformat(event["event_timestamp"])
                )
            )
        finally:
            cursor.close()
        
