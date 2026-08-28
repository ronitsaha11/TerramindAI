# TerraMind AI

Earth Intelligence Platform — an interactive map backed by a real dataset
registry and a PostGIS spatial query engine.

## Architecture

- **Frontend**: `frontend/` — Vite + React + MapLibre GL + Zustand + TanStack Query
- **Backend API**: `apps/backend/` — FastAPI
- **Database**: PostgreSQL + PostGIS
- **Cache/Queue**: Redis + Celery
- **ML**: PyTorch / transformers (SegFormer), currently backend-only

> `apps/frontend/` is a dead Next.js scaffold kept only for history. The active
> frontend is the root-level `frontend/` directory. Do not build there.

## Prerequisites

- Node.js 18+ and **pnpm** (not npm)
- Python 3.13 with a virtualenv at `apps/backend/.venv`
- Docker Desktop

## Running the stack

Windows, from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_stack.ps1
```

That starts the containers, applies migrations, launches the Celery worker and
the API, then the Vite dev server — verifying each layer before continuing.

| Service  | URL                                      |
| -------- | ---------------------------------------- |
| Frontend | http://localhost:5173                    |
| API docs | http://127.0.0.1:8000/docs               |
| Health   | http://127.0.0.1:8000/api/v1/health      |

To stop:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_stack.ps1
```

Containers are left running so the database keeps its data; pass `-Containers`
to stop those too.

### Notes

- Celery must run with `--pool=solo` on Windows or it dies on billiard
  permission errors. The start script does this for you.
- Only `db` and `redis` are containerised. The API and frontend run natively.
- Copy `.env.example` to `.env` before the first run.

## Spatial queries

Dataset features are stored as real PostGIS geometries with a GiST index. Three
query modes are exposed from the Datasets panel, each rendered in a distinct
colour so results never get confused with each other:

| Query      | Endpoint                       | Predicate                                        |
| ---------- | ------------------------------ | ------------------------------------------------ |
| Nearby     | `GET .../query/nearby`         | `ST_DWithin` — both sides cast to `::geography`   |
| Contains   | `GET .../query/contains`       | `ST_Contains` from a clicked polygon              |
| Intersects | `GET .../query/intersects`     | `ST_Intersects` against a second dataset          |

The `::geography` cast on `ST_DWithin` is required — without it the radius is
measured in degrees, not metres.
