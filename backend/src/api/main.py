
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.database.repository import DatabaseRepository
from src.pipeline import run_pipeline, INPUT_FILE


app = FastAPI(
    title="CDC Data Engineering Pipeline API",
    description="API for monitoring CDC pipeline execution and customer data",
    version="1.0.0"
)


# Allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "CDC Pipeline API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/pipeline-runs")
def get_pipeline_runs():
    repository = DatabaseRepository()
    cursor = repository.connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM pipeline_runs
            ORDER BY start_time DESC
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        repository.close()


@app.get("/customers")
def get_customers():
    repository = DatabaseRepository()
    cursor = repository.connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM customers_current
            ORDER BY customer_id
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        repository.close()


@app.get("/rejected-events")
def get_rejected_events():
    repository = DatabaseRepository()
    cursor = repository.connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM rejected_events
            ORDER BY rejected_at DESC
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        repository.close()


@app.get("/statistics")
def get_statistics():
    repository = DatabaseRepository()
    cursor = repository.connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM customers_current)
                    AS total_customers,

                (SELECT COUNT(*) FROM customer_event_history)
                    AS total_history_events,

                (SELECT COUNT(*) FROM processed_events)
                    AS total_processed_events,

                (SELECT COUNT(*) FROM rejected_events)
                    AS total_rejected_events,

                (SELECT COUNT(*) FROM pipeline_runs)
                    AS total_pipeline_runs
        """)

        return cursor.fetchone()

    finally:
        cursor.close()
        repository.close()


@app.post("/run-pipeline")
def trigger_pipeline():
    try:
        # Execute the existing ETL pipeline
        run_id = run_pipeline(INPUT_FILE)

        # Retrieve the completed execution details
        repository = DatabaseRepository()
        cursor = repository.connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT *
                FROM pipeline_runs
                WHERE run_id = %s
            """, (run_id,))

            result = cursor.fetchone()

            if result is None:
                raise HTTPException(
                    status_code=500,
                    detail="Pipeline run record not found"
                )

            return result

        finally:
            cursor.close()
            repository.close()

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
