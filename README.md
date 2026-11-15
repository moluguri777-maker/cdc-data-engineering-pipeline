# CDC Data Engineering Pipeline

An end-to-end Change Data Capture (CDC) pipeline built using Python, MySQL, FastAPI, and React.

The pipeline ingests customer events from JSON files, validates incoming records, processes INSERT, UPDATE, and DELETE operations, maintains the latest customer state, and tracks event-level processing history.

An interactive dashboard provides visibility into pipeline executions, customer records, rejected events, and database statistics.

## Architecture

```text
             JSON Event Source
                     |
                     v
                 Ingestion
                     |
                     v
                 Validation
                     |
              +------+------+
              |             |
            Valid         Invalid
              |             |
              v             v
         CDC Processor  Rejected Events
              |
       +------+------+------+
       |             |       |
       v             v       v
 Customers       Event    Processed
 Current         History   Events
       |
       v
     MySQL
       |
       v
    FastAPI
       |
       v
 React Dashboard
```

## Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python |
| API | FastAPI |
| Database | MySQL 8.0 |
| Frontend | React, JavaScript, Vite |
| Testing | Pytest |
| Version Control | Git, GitHub |

## Key Features

- **Event Ingestion:** Reads customer events from JSON files.
- **Data Validation:** Validates incoming records and identifies invalid events.
- **CDC Processing:** Supports INSERT, UPDATE, and DELETE operations.
- **Deduplication:** Detects duplicate events using event identifiers.
- **Version Management:** Handles out-of-order and stale events using source versions.
- **Customer State Management:** Maintains the latest customer state in MySQL.
- **Event History:** Preserves processed customer events for historical tracking.
- **Rejected Event Tracking:** Stores invalid events with rejection reasons.
- **Idempotency:** Prevents previously processed events from being applied again.
- **Execution Monitoring:** Records pipeline execution status and processing metrics.
- **Interactive Dashboard:** Displays pipeline runs, customer records, rejected events, and database statistics.

## Database Design

The pipeline uses five MySQL tables:

| Table | Purpose |
|---|---|
| `pipeline_runs` | Tracks pipeline execution details, status, and metrics |
| `customers_current` | Stores the latest state of each customer |
| `customer_event_history` | Maintains customer event history |
| `processed_events` | Tracks processed event IDs and processing status |
| `rejected_events` | Stores rejected events and their rejection reasons |

The complete database structure, including primary keys, foreign keys, indexes, and constraints, is available in `backend/src/database/schema.sql`.

## Project Structure

```text
cdc-data-engineering-pipeline/
│
├── backend/
│   ├── config/
│   │   └── database.py
│   │
│   ├── data/
│   │   ├── incoming/
│   │   ├── processed/
│   │   └── rejected/
│   │
│   ├── scripts/
│   │   └── generate_events.py
│   │
│   ├── src/
│   │   ├── api/
│   │   │   └── main.py
│   │   ├── database/
│   │   │   ├── repository.py
│   │   │   ├── schema.sql
│   │   │   └── test_repository.py
│   │   ├── ingestion/
│   │   ├── transformation/
│   │   ├── validation/
│   │   └── pipeline.py
│   │
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

## Setup and Installation

### Prerequisites

- Python 3.10 or later
- MySQL 8.0
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/moluguri777-maker/cdc-data-engineering-pipeline.git
cd cdc-data-engineering-pipeline
```

### 2. Set up the Python backend

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure MySQL

Create the database:

```sql
CREATE DATABASE cdc_pipeline_test;
```

Execute the SQL schema in `backend/src/database/schema.sql` to create the five required tables.

### 4. Configure environment variables

Create a `.env` file inside the backend directory:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cdc_pipeline_test
```

Replace the placeholder password with your MySQL password.

### 5. Start the FastAPI backend

From the `backend` directory:

```bash
uvicorn src.api.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs

### 6. Start the React frontend

Open another terminal:

```bash
cd frontend

npm install

npm run dev
```

Frontend dashboard: http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API health message |
| GET | `/health` | Health check |
| GET | `/statistics` | Dashboard database metrics |
| GET | `/pipeline-runs` | Pipeline execution history |
| GET | `/customers` | Current customer records |
| GET | `/rejected-events` | Rejected event records |
| POST | `/run-pipeline` | Triggers the CDC pipeline |

## Running Tests

From the backend directory, activate the virtual environment and run:

```bash
python -m pytest -v
```

## Future Improvements

- Scheduled and automated pipeline execution
- Support for additional event sources
- Improved pipeline observability and logging
- Scalable batch processing
- Docker-based deployment
- Cloud database integration

## Author

**Moluguri Pranitha**

GitHub: [moluguri777-maker](https://github.com/moluguri777-maker)

Project Repository: [CDC Data Engineering Pipeline](https://github.com/moluguri777-maker/cdc-data-engineering-pipeline)
