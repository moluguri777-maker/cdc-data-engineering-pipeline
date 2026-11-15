
class CDCProcessor:
    """
    Processes Change Data Capture (CDC) events.

    Maintains:
    - Customer current state
    - Historical event records
    - Processed event tracking
    - Out-of-order event handling
    - Duplicate protection
    """

    def __init__(self, repository):
        self.repository = repository

    # ==========================================
    # PROCESS A SINGLE EVENT
    # ==========================================

    def process_event(self, event, run_id):

        connection = self.repository.connection

        try:
            # Start atomic database transaction
            connection.start_transaction()

            event_id = event["event_id"]
            customer_id = event["customer_id"]
            operation = event["operation"]
            version = event["source_version"]

            # ----------------------------------
            # 1. Check duplicate event
            # ----------------------------------

            if self.repository.is_event_processed(event_id):
                connection.rollback()
                return "DUPLICATE"

            # ----------------------------------
            # 2. Retrieve current customer state
            # ----------------------------------

            current = self.repository.get_customer(customer_id)

            # ----------------------------------
            # 3. Check customer version conflict
            # ----------------------------------

            existing_version = (
                self.repository.get_event_by_customer_version(
                    customer_id,
                    version
                )
            )

            if existing_version:

                self.repository.save_rejected_event(
                    event,
                    run_id,
                    "Conflicting event: customer version already exists"
                )

                connection.commit()
                return "REJECTED"

            # ----------------------------------
            # 4. Handle out-of-order events
            # ----------------------------------

            if current is not None:

                current_version = current["source_version"]

                if version < current_version:

                    # Preserve stale event in history
                    self.repository.save_event_history(
                        event,
                        run_id
                    )

                    self.repository.save_processed_event(
                        event,
                        run_id,
                        "STALE"
                    )

                    connection.commit()
                    return "STALE"

                if version == current_version:

                    self.repository.save_rejected_event(
                        event,
                        run_id,
                        "Conflicting event at current customer version"
                    )

                    connection.commit()
                    return "REJECTED"

            # ----------------------------------
            # 5. Apply INSERT operation
            # ----------------------------------

            if operation == "INSERT":

                self.repository.upsert_customer(event)

            # ----------------------------------
            # 6. Apply UPDATE operation
            # ----------------------------------

            elif operation == "UPDATE":

                self.repository.upsert_customer(event)

            # ----------------------------------
            # 7. Apply DELETE operation
            # ----------------------------------

            elif operation == "DELETE":

                if current is None:

                    # DELETE arrived before INSERT.
                    # Create a tombstone.
                    self.repository.create_tombstone(event)

                else:

                    self.repository.mark_customer_deleted(event)

            # ----------------------------------
            # 8. Preserve event history
            # ----------------------------------

            self.repository.save_event_history(
                event,
                run_id
            )

            # ----------------------------------
            # 9. Record processed event
            # ----------------------------------

            self.repository.save_processed_event(
                event,
                run_id,
                "PROCESSED"
            )

            # All operations succeeded
            connection.commit()

            return "PROCESSED"

        except Exception:
            connection.rollback()
            raise

    # ==========================================
    # PROCESS MULTIPLE EVENTS
    # ==========================================

    def process_events(self, events, run_id):

        results = {
            "PROCESSED": 0,
            "STALE": 0,
            "DUPLICATE": 0,
            "REJECTED": 0,
            "FAILED": 0
        }

        for event in events:

            try:

                status = self.process_event(
                    event,
                    run_id
                )

                results[status] += 1

            except Exception as error:

                results["FAILED"] += 1

                print(
                    f"Event processing failed: "
                    f"{event.get('event_id', 'UNKNOWN')} "
                    f"| Error: {error}"
                )

        return results
