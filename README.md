\# CDC Data Engineering Pipeline



An end-to-end Change Data Capture (CDC) pipeline built using \*\*Python, MySQL, FastAPI, and React\*\*. The project ingests customer events, validates records, processes INSERT, UPDATE, and DELETE operations, maintains customer state, and tracks event-level processing history.



The application also provides an interactive dashboard for monitoring pipeline executions, customer records, and rejected events.



\## Architecture



```text

&#x20;          JSON Event Source

&#x20;                  |

&#x20;                  v

&#x20;             Ingestion

&#x20;                  |

&#x20;                  v

&#x20;             Validation

&#x20;                  |

&#x20;            +-----+-----+

&#x20;            |           |

&#x20;         Valid       Invalid

&#x20;            |           |

&#x20;            v           v

&#x20;       CDC Processor  Rejected Events

&#x20;            |

&#x20;      +-----+------------------+

&#x20;      |          |             |

&#x20;      v          v             v

&#x20;Customers    Event History  Processed Events

&#x20;Current

&#x20;      |

&#x20;      v

&#x20;    MySQL

&#x20;      |

&#x20;      v

&#x20;   FastAPI

&#x20;      |

&#x20;      v

&#x20;React Dashboard

```



\## Technology Stack



| Layer | Technologies |

|---|---|

| Backend | Python |

| API | FastAPI |

| Database | MySQL 8.0 |

| Frontend | React, JavaScript, Vite |

| Testing | Pytest |

| Version Control | Git, GitHub |



\## Key Features



\- \*\*Event Ingestion:\*\* Reads customer events from JSON files.

\- \*\*Data Validation:\*\* Validates incoming records and identifies invalid events.

\- \*\*CDC Processing:\*\* Supports INSERT, UPDATE, and DELETE operations.

\- \*\*Deduplication:\*\* Detects duplicate events using event identifiers.

\- \*\*Version Management:\*\* Handles out-of-order and stale events using source versions.

\- \*\*Customer State Management:\*\* Maintains the latest customer state in MySQL.

\- \*\*Event History:\*\* Preserves processed customer events for historical tracking.

\- \*\*Rejected Event Tracking:\*\* Stores invalid and rejected events with rejection reasons.

\- \*\*Idempotency:\*\* Prevents previously processed events from being applied again.

\- \*\*Execution Monitoring:\*\* Records pipeline execution status and processing metrics.

\- \*\*Interactive Dashboard:\*\* Displays pipeline runs, customer records, rejected events, and database statistics.



\## Database Design



The pipeline uses five MySQL tables:



| Table | Purpose |

|---|---|

| `pipeline\_runs` | Tracks pipeline execution details, status, and metrics |

| `customers\_current` | Stores the latest state of each customer |

| `customer\_event\_history` | Maintains customer event history |

| `processed\_events` | Tracks processed event IDs and processing status |

| `rejected\_events` | Stores rejected events and their rejection reasons |



The complete database structure, including primary keys, foreign keys, indexes, and constraints, is available in:



`backend/src/database/schema.sql`



\## Project Structure



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

│   │   └── generate\_events.py

│   │

│   ├── src/

│   │   ├── api/

│   │   │   └── main.py

│   │   ├── database/

│   │   │   ├── repository.py

│   │   │   ├── schema.sql

│   │   │   └── test\_repository.py

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



\## Setup and Installation



\### Prerequisites



\- Python 3.10 or later

\- MySQL 8.0

\- Node.js and npm

\- Git



\### 1. Clone the repository



```bash

git clone https://github.com/moluguri777-maker/cdc-data-engineering-pipeline.git



cd cdc-data-engineering-pipeline

```



\### 2. Configure the Python backend



```bash

cd backend



python -m venv venv



venv\\Scripts\\activate



pip install -r requirements.txt

```



\### 3. Configure MySQL



Create the database:



```sql

CREATE DATABASE cdc\_pipeline\_test;

```



Execute the SQL schema from:



`backend/src/database/schema.sql`



This creates the five required tables.



\### 4. Configure environment variables



Create a `.env` file inside the backend directory with your MySQL connection settings:



```env

DB\_HOST=127.0.0.1

DB\_PORT=3306

DB\_USER=root

DB\_PASSWORD=your\_password

DB\_NAME=cdc\_pipeline\_test

```



Replace the placeholder password with your own MySQL password.



\### 5. Start the FastAPI backend



From the `backend` directory:



```bash

uvicorn src.api.main:app --reload

```



Backend API:



`http://127.0.0.1:8000`



Interactive API documentation:



`http://127.0.0.1:8000/docs`



\### 6. Start the React frontend



Open another terminal:



```bash

cd frontend



npm install



npm run dev

```



Frontend dashboard:



`http://localhost:5173`



\## API Endpoints



| Method | Endpoint | Description |

|---|---|---|

| GET | `/` | API health message |

| GET | `/health` | Health check |

| GET | `/statistics` | Dashboard database metrics |

| GET | `/pipeline-runs` | Pipeline execution history |

| GET | `/customers` | Current customer records |

| GET | `/rejected-events` | Rejected event records |

| POST | `/run-pipeline` | Triggers the CDC pipeline |



\## Running Tests



From the backend directory, activate the virtual environment and execute:



```bash

python -m pytest -v

```



\## Future Improvements



\- Scheduled and automated pipeline execution

\- Support for additional event sources

\- Improved pipeline observability and logging

\- Scalable batch processing

\- Docker-based deployment

\- Cloud database integration



\## Author



\*\*Pranitha Moluguri\*\*



GitHub: \[moluguri777-maker](https://github.com/moluguri777-maker)



Project Repository: \[CDC Data Engineering Pipeline](https://github.com/moluguri777-maker/cdc-data-engineering-pipeline)

