# Traffic Analysis Microservice

A FastAPI microservice for geospatial traffic analytics. Ingests historical speed data from Parquet files, stores it in a PostGIS-enabled PostgreSQL database, and exposes REST endpoints for aggregated speed analysis, slow link detection, and spatial filtering.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Pydantic v2 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 15 + PostGIS 3.4 |
| Spatial | GeoAlchemy2, ST_Intersects, ST_AsText |
| Ingestion | Pandas, PyArrow, Polars |
| Testing | Pytest, Starlette TestClient |
| Runtime | Docker, Uvicorn |

## Architecture Overview

```mermaid
flowchart TD
    subgraph DATA["📦 Data Layer"]
        P1[link_info.parquet]
        P2[speed_data.parquet]
        P1 & P2 --> ING[ingest_data.py]
    end

    subgraph DB["🗄️ Database — PostgreSQL + PostGIS"]
        ING --> LNK["Link\n(id, road_name, geometry LINESTRING)"]
        ING --> SR["SpeedRecord\n(link_id, speed, day_of_week, time_period)"]
    end

    subgraph APP["⚙️ Application Layer — FastAPI"]
        LNK & SR --> SVC["AnalyticsService\n(aggregation · slow links · spatial filter)"]
        SVC --> R1["GET /aggregates/"]
        SVC --> R2["GET /aggregates/{link_id}"]
        SVC --> R3["POST /aggregates/spatial_filter"]
        SVC --> R4["GET /patterns/slow_links"]
    end

    subgraph CLIENT["🖥️ Client Layer"]
        R1 & R3 --> NB["Jupyter Notebook\n(requests → WKT → GeoJSON → Mapbox)"]
    end
```

The **API layer** handles HTTP concerns (validation, routing, pagination params).  
The **service layer** owns all query logic — it is independently testable without the HTTP stack.

## Project Structure

```
urbansdk-homework/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── aggregates.py     # /aggregates routes
│   │   │   └── patterns.py       # /patterns routes
│   │   ├── api.py                # Router registration
│   │   └── dependencies.py       # DB session dependency
│   ├── core/
│   │   └── config.py             # Settings (DATABASE_URL, etc.)
│   ├── db/
│   │   └── session.py            # SQLAlchemy engine + SessionLocal
│   ├── models/
│   │   ├── link.py               # Link ORM model (PostGIS geometry)
│   │   └── speed_record.py       # SpeedRecord ORM model
│   ├── schemas/
│   │   ├── enums.py              # DayOfWeek, TimePeriod enums
│   │   ├── link.py               # LinkResponse, AggregateResponse
│   │   ├── spatial.py            # SpatialFilter (bounding box)
│   │   └── speed_record.py       # SpeedRecordResponse
│   ├── services/
│   │   └── analytics.py          # AnalyticsService (all query logic)
│   └── main.py                   # FastAPI app entrypoint
├── scripts/
│   └── ingest_data.py            # ETL: parquet → PostgreSQL
├── notebooks/
│   └── traffic_visualization.ipynb
├── tests/
│   ├── api/
│   │   ├── test_aggregates.py
│   │   └── test_patterns.py
│   ├── services/
│   │   └── test_analytics.py
│   └── conftest.py               # Fixtures, isolated test DB setup
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Setup

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Using uv (faster)

```bash
uv venv
uv pip install -r requirements.txt
```

## Running the Application

### With Docker (recommended)

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Locally (without Docker)

Ensure PostgreSQL with PostGIS is running, then set your `DATABASE_URL`:

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/traffic_db
uvicorn app.main:app --reload
```

### Ingest Data from parquet

```bash
# Inside the running api container
docker compose exec api python scripts/ingest_data.py
```

## Running Tests

Tests run against an isolated `traffic_test_db` database (not the development DB).

```bash
# Create the test database once
docker compose exec db psql -U postgres -c 'CREATE DATABASE traffic_test_db;'
docker compose exec db psql -U postgres -d traffic_test_db -c 'CREATE EXTENSION postgis;'

# Run the full test suite
docker compose exec api pytest tests/
```

The test suite uses transactional rollbacks — each test gets a fresh state and leaves no data behind.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/aggregates/` | Average speed per link. Supports `day`, `period`, `limit`, `offset` filters. |
| `GET` | `/aggregates/{link_id}` | Detailed speeds for a specific link. |
| `POST` | `/aggregates/spatial_filter` | Links within a bounding box, optionally filtered by day/period. |
| `GET` | `/patterns/slow_links` | Links consistently below a speed threshold. |

All temporal filters accept enum values: `day` = `Monday`…`Sunday`, `period` = `AM Peak`, `PM Peak`, `Midday`, `Evening`, `Overnight`.

**Example:**
```bash
curl "http://localhost:8000/aggregates/?day=Monday&period=AM+Peak&limit=10"
```

## Jupyter Notebook

A visualization notebook is included at `notebooks/traffic_visualization.ipynb`.

```bash
uv pip install jupyter mapboxgl shapely
uv run jupyter notebook notebooks/traffic_visualization.ipynb
```

Set your `MAPBOX_TOKEN` in the Setup cell, then run all cells. The notebook calls the API, converts WKT geometry to GeoJSON, and renders a choropleth speed map over Jacksonville, FL.

## Key Design Decisions

**Aggregation at query time, not storage time**  
Average speeds are computed via `AVG()` in SQL on each request. This avoids stale pre-computed data and keeps the schema simple. For significantly larger datasets, materialized views would be the right optimization.

**PostGIS for spatial queries**  
Bounding box queries use `ST_Intersects(geometry, ST_MakeEnvelope(...))` with a GiST spatial index. This offloads spatial computation to the database layer where it runs efficiently — far better than fetching all rows and filtering in Python.

**Geometry as WKT in responses**  
`ST_AsText(geometry)` converts PostGIS binary geometry to readable WKT strings (`LINESTRING(...)`). This avoids binary serialization issues across the API boundary and is directly consumable by `shapely` in the notebook.

**SQLEnum with `native_enum=False`**  
Day and period fields use `CHECK` constraints instead of PostgreSQL native `ENUM` types. This avoids complex Alembic migrations when enum values change and is fully introspectable by SQLAlchemy.

**Service layer separation**  
`AnalyticsService` is a plain static class with no FastAPI dependencies. Tests in `tests/services/` call it directly with a real DB session — validating query logic independently of HTTP routing.

## Tradeoffs and Assumptions

- **No Alembic migrations**: `Base.metadata.create_all()` is used for simplicity. For production, schema evolution should be managed via Alembic.
- **No authentication**: The API is open. Production would require OAuth2 or API key middleware.
- **In-memory geometry conversion**: WKT→GeoJSON is done in the notebook client, not the API. This is intentional — the API stays geometry-format agnostic.
- **Single-region dataset**: Data is scoped to Duval County, FL (January 2024). The spatial index and query planner are tuned for this scale (~1.2M records).

## Future Improvements

- **Alembic migrations** for schema versioning
- **Materialized views** for pre-computed peak-hour aggregates
- **Redis caching** on heavy aggregate endpoints with short TTLs
- **Authentication** via OAuth2 / API keys
- **Rate limiting** via `slowapi`
- **Async SQLAlchemy** for higher concurrency under load
