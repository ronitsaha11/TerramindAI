# TerraMind AI — Backend Boot + Map Rendering Recovery

Task: resolve the backend boot failure, the rasterio blocker, and the unverified
map rendering pipeline. No new features. Phase 5 (AI/NL query) untouched.

**Legend**

| Mark | Meaning |
| --- | --- |
| ✅ | VERIFIED WORKING — observed directly, with evidence |
| ⚠️ | CODE EXISTS BUT NOT VERIFIED |
| ❌ | BROKEN |
| 🚧 | BLOCKED BY ENVIRONMENT |

---

## 1. Initial diagnostic findings

| # | Finding | Status |
| --- | --- | --- |
| 1 | Framework is FastAPI; entry `apps/backend/src/main.py`, module-level `app = create_app()` (line 111) | ✅ |
| 2 | Health endpoints: `GET /api/v1/health` (static), `GET /api/v1/ready` (checks Postgres + Redis) | ✅ |
| 3 | Storage: PostgreSQL/PostGIS via SQLAlchemy async + asyncpg; Redis for Celery. Both containers running | ✅ |
| 4 | rasterio is imported in exactly two modules | ✅ |
| 5 | `api/dependencies.py` is imported by every router and eagerly imported both rasterio modules at module scope | ❌ |
| 6 | Dataset/project/spatial endpoints have no rasterio dependency (`get_dataset_service` → UnitOfWork only) | ✅ |
| 7 | CORS allowed only port 5173, but the frontend now runs on 5273 | ❌ |
| 8 | Real data already present — no fixture needed to be created | ✅ |

rasterio import sites:

```
src/analytics/providers/cog_provider.py:4-6
src/geospatial/polygonizer.py:4
```

---

## 2. Root cause — backend boot failure

The **first** real exception, traced rather than assumed:

```
main.py:11              from src.api.v1.router import api_router
router.py:3             from src.api.v1.ai import router as ai_router
ai.py:13                from src.api.dependencies import ...
dependencies.py:18      from src.analytics.providers.cog_provider import COGRasterProvider
cog_provider.py:4       import rasterio
rasterio/__init__.py:37 from rasterio._base import DatasetBase
ImportError: DLL load failed while importing _base:
An Application Control policy has blocked this file.
```

**The root cause is an architectural coupling, not a missing feature.**
`api/dependencies.py` is imported by every router, and it imported two
rasterio-backed concrete classes at module scope. One unloadable binary
therefore made the entire API unimportable — including endpoints that never
touch raster data.

rasterio is **not** architecturally required at startup.

---

## 3. Root cause — rasterio blocker

🚧 **BLOCKED BY ENVIRONMENT. Not a repository defect.**

Evidence gathered:

| Check | Result |
| --- | --- |
| `.pyd` present on disk | Yes — `_base.cp313-win_amd64.pyd`, 287 KB |
| Other native modules (numpy, shapely, asyncpg, pyproj, torch, pydantic_core) | All import fine |
| Fresh install of latest rasterio in a clean venv | Blocked identically |
| `HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy` → `VerifiedAndReputablePolicyState` | `1` = Smart App Control **ON, enforcing** |

So this is not a version, wheel, GDAL, PATH or venv problem. Windows **Smart App
Control** is blocking that specific unsigned binary. Smart App Control has **no
exclusion mechanism** and, once disabled, cannot be re-enabled without
reinstalling Windows — so it was left untouched.

Host-level options, all the user's decision:

1. Disable Smart App Control (irreversible).
2. Run the backend in Docker or WSL, where the host policy does not apply.
3. Obtain a rasterio build whose binary the policy trusts.

---

## 4. Was rasterio repaired or isolated?

**Isolated. Not repaired.** ✅ for isolation, 🚧 for the underlying environment.

`api/dependencies.py` now imports the rasterio-backed classes **inside** their
provider functions, and converts a failed import into a clear HTTP 503:

```python
def get_raster_provider() -> RasterProvider:
    try:
        from src.analytics.providers.cog_provider import COGRasterProvider
    except ImportError as exc:
        raise _raster_dependency_unavailable(exc) from exc
    return COGRasterProvider()
```

`get_polygonizer` is annotated against the pre-existing `PolygonizerProtocol`
(from `geospatial/interfaces.py`) so type information survives without importing
the binary. `RasterProvider` in `analytics/providers/base.py` has no rasterio
import, so that annotation was already safe.

Resulting behaviour:

```
CORE BACKEND ─┬─ vector / dataset / spatial endpoints  → work ✅
              └─ raster analytics                      → HTTP 503, clear message ✅
```

Observed:

```
POST /api/v1/analysis            → 503
POST /api/v1/geospatial/vectorize → 503
"Raster analytics are unavailable because the 'rasterio' native extension
 could not be loaded: DLL load failed while importing _base: An Application
 Control policy has blocked this file.. Vector dataset and spatial query
 endpoints are unaffected."
```

**No rasterio functionality was faked or stubbed.** When rasterio can load, the
providers behave exactly as before.

---

## 5. Backend startup command

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_stack.ps1
```

Or the backend alone:

```powershell
cd apps\backend
$env:PYTHONPATH = (Get-Item .).FullName
.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000
```

Requires: Docker containers `db` + `redis`, venv at `apps/backend/.venv`
(Python 3.13), `apps/backend/.env`. Celery must use `--pool=solo` on Windows.

Startup log (no traceback): ✅

```
Starting TerraMind AI in development mode.
Redis client connected.
Application startup complete.
Uvicorn running on http://127.0.0.1:8000
```

---

## 6. API endpoints tested

All tested with real HTTP requests. ✅

| METHOD | URL | STATUS | RESPONSE SHAPE | RESULT |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/health` | 200 | `SuccessResponse[dict]` n=1 | NON-EMPTY |
| GET | `/api/v1/ready` | 200 | `SuccessResponse[dict]` n=3 | NON-EMPTY |
| GET | `/api/v1/projects` | 200 | `SuccessResponse[list]` n=3 | NON-EMPTY |
| GET | `/api/v1/projects/{pid}/datasets` | 200 | `SuccessResponse[list]` n=4 | NON-EMPTY |
| GET | `/api/v1/projects/{pid}/datasets/{did}/geojson` | 200 | `FeatureCollection` | 1188 features |
| GET | `.../query/contains?feature_id=…` | 200 | `FeatureCollection` | 1 feature |
| GET | `.../query/nearby?lon&lat&radius_meters` | 200 | `FeatureCollection` | 74 features |
| GET | `/api/v1/jobs` | 200 | `list` | — |
| POST | `/api/v1/analysis` | 503 | error envelope | graceful ✅ |
| POST | `/api/v1/geospatial/vectorize` | 503 | error envelope | graceful ✅ |
| GET | `.../datasets/x/geojson` (bad UUID) | 422 | validation error | correct ✅ |

28 routes total in the OpenAPI schema.

---

## 7. Dataset used for verification

Pre-existing; nothing new was created. ✅

- **`bangalore osm`** — `86366ad9-9947-4096-a7db-44be16050193`, **1,188 features**
  (672 parks, 473 hospitals, 43 stations), extent `[77.4088, 12.8002, 77.6004, 13.0004]`
- Also present: 3 × `test data` (3 features each)
- On disk: `datasets/bangalore_osm.geojson` (380 KB)

---

## 8. Frontend → backend request path

Traced end to end. ✅

```
useDatasetManager / MapLibreDatasetRenderer
  VITE_API_BASE_URL = http://127.0.0.1:8000/api/v1
      ↓
GET /projects                          → 200
GET /projects/{pid}/datasets           → 200   (SuccessResponse.data → IDataset[])
GET /projects/{pid}/datasets/{did}/geojson → 200 (FeatureCollection)
      ↓
MapLibre GeoJSON source  dataset-source-{id}
      ↓
layers: dataset-fill / dataset-line / dataset-circle
      ↓
rendered features
```

Browser-observed network (from `localhost:5273`, cross-origin to `127.0.0.1:8000`):
all **200 OK**, confirming CORS is correct after the fix.

Contract checks: response is `{success, data}` for lists and a bare
`FeatureCollection` for geometry — both matched by the frontend parsers. No
Feature/FeatureCollection mismatch, no undefined properties, no empty arrays.

---

## 9. Map rendering root cause

❌ **A second real blocker existed: CORS.**

`apps/backend/.env` allowed only `http://localhost:5173`, but the frontend was
moved to **5273** (5173 is occupied by an unrelated project on this machine).
Every browser request would have been blocked while `curl` kept working — the
classic "API works but the map is empty" failure.

Fixed by adding both 5273 origins (5173 retained):

```
ALLOWED_ORIGINS='["http://localhost:5273", "http://127.0.0.1:5273",
                  "http://localhost:5173", "http://127.0.0.1:5173"]'
```

Beyond that, **no rendering defect was found.** Verified on the live map:

| Check | Result |
| --- | --- |
| Canvas non-zero | 1296 × 874 ✅ |
| Container non-zero | 1296 × 874 ✅ |
| Map initializes | `engineState = "ready"` ✅ |
| Base map renders | 93 style layers, CARTO tiles ✅ |
| Dataset layers present | fill / line / circle ✅ |
| Source features | 1,188 ✅ |
| Invalid geometries | **0** ✅ |
| CRS | WGS-84 lon/lat, footer `EPSG:4326` ✅ |
| Data bounds | `[77.4088, 12.8002, 77.6004, 13.0004]` ✅ |
| Features inside viewport | viewport `[77.28, 12.78 → 77.67, 13.03]` contains data ✅ |
| Layer visibility | visible ✅ |
| Layer opacity | fill 0.4, line 1, circle 1 — all non-zero ✅ |
| Rendered features | circle 432, fill 747, line 748 ✅ |

**Note on the "INITIALIZING ENGINE" overlay:** it persists only when the browser
pane is hidden. `EarthEngine` sets state `ready` inside `map.once('load')`, and
that event never fires while the page is not compositing (MapLibre's render loop
is `requestAnimationFrame`-driven). Forcing render passes made it fire
immediately with no exception. In a normally displayed browser it does not occur
— confirmed by the user's screenshot. **Artifact, not a bug.** ✅

---

## 10. Dataset styling root cause

**No defect found.** ✅ The compiled paint expression on the live map:

```json
["case",
 ["==",["to-string",["get","category"]],"park"],     "rgba(230, 159, 0, 1.000)",
 ["==",["to-string",["get","category"]],"hospital"], "rgba(86, 180, 233, 1.000)",
 ["==",["to-string",["get","category"]],"station"],  "rgba(0, 158, 115, 1.000)",
 "rgba(120, 120, 120, 1.000)"]
```

| Expected | Actual | Status |
| --- | --- | --- |
| parks → orange | `rgba(230,159,0)` | ✅ visible on map |
| hospitals → blue | `rgba(86,180,233)` | ✅ visible on map |
| stations → green | `rgba(0,158,115)` | ✅ visible on map |
| unknown → grey | `rgba(120,120,120)` | ⚠️ **not exercised** |

⚠️ The grey fallback is **unproven**: all 1,188 features carry a `category`, so
nothing falls through to the default branch. The branch exists in the compiled
expression but no feature currently takes it.

An earlier framebuffer pixel count appeared to show ~11.6k "grey" pixels; on
review those are basemap greys within the sampling tolerance, **not** styled
features. Recorded here so the earlier number is not mistaken for evidence.

---

## 11. Files changed

| File | Change | Tracked? |
| --- | --- | --- |
| `apps/backend/src/api/dependencies.py` | Lazy rasterio imports in `get_raster_provider` / `get_polygonizer`; `_raster_dependency_unavailable` → HTTP 503; annotate via `PolygonizerProtocol`; import sort | Yes |
| `apps/backend/.env` | Added 5273 origins to `ALLOWED_ORIGINS` | No — gitignored, local only |

Two files. No architecture removed: the dataset registry, spatial engine,
styling engine, `RasterProvider` ABC, `PolygonizerProtocol`, `COGRasterProvider`
and `RasterPolygonizer` are all intact and unmodified.

**Nothing was committed or pushed.**

---

## 12. Commands executed

```bash
# diagnosis
python -c "import src.main"                       # first-exception trace
grep -rn "import rasterio" src/                   # import sites
python -c "import numpy, shapely, asyncpg, torch" # scope of the block
python -m venv rioenv && pip install rasterio     # clean-venv reproduction

# fix + verify
python -c "import src.main"                       # boots after isolation
python -m uvicorn src.main:app --port 8000
curl .../api/v1/health  .../projects  .../datasets  .../geojson
curl -X POST .../api/v1/analysis                  # 503 degradation

# gates
pnpm lint && pnpm type-check && pnpm build
python -m ruff check . && python -m ruff format --check . && python -m mypy src/
```

---

## 13. Runtime verification results

| Criterion | Status | Evidence |
| --- | --- | --- |
| Backend boots | ✅ | uvicorn PID alive, no traceback |
| Health endpoint responds | ✅ | `GET /api/v1/health` → 200 |
| Dataset API returns real data | ✅ | 1,188-feature FeatureCollection |
| Frontend ↔ backend communication | ✅ | 4 browser requests, all 200, cross-origin |
| 2D map renders | ✅ | CARTO basemap + street network |
| Real features appear | ✅ | 1,179 rendered at z11.2 |
| Geographically correct | ✅ | over Bengaluru, matching data bounds |
| Styling visibly applied | ✅ | orange / blue / green on screen |
| Pan works | ✅ | centre `77.6242,12.8276 → 77.7437,12.7547`; rendered 732 → 86 |
| Zoom works | ✅ | z13 → 198 features; z9.5 → 779; bounds change |
| No infinite loading | ✅ | overlay cleared, `engineState = ready` |
| No fatal console errors | ✅ | zero errors |
| Network requests succeed | ✅ | all 200 |
| rasterio no longer blocks core backend | ✅ | boots and serves without it |
| Architecture intact | ✅ | two files touched, nothing removed |
| Phase 5 untouched | ✅ | no LLM/NL/AI work performed |

**How visual verification was obtained — stated plainly:** the automated browser
pane in this environment is not displayed, so it never composites frames and
screenshots time out. I could not capture the map myself. The visual confirmation
comes from **a screenshot supplied by the user**, which shows the 2D map with
orange parks, blue hospitals and green stations over Bengaluru, the URL on
`localhost:5273`, and the footer reading `EPSG:4326 / 12.900367° N /
77.504605° E / zoom 11.22 / 159 FPS / ONLINE`.

Everything else above was verified programmatically against the live map
instance. Where the hidden pane paused MapLibre's render loop, render passes were
driven manually **only to make the automated checks possible** — this is a
harness workaround, not application behaviour, and not a change to the app.

---

## 14. Remaining blockers

1. 🚧 **rasterio cannot load on this machine.** Smart App Control blocks its
   native extension. Raster analytics (`POST /analysis`,
   `POST /geospatial/vectorize`, the Celery vectorize task) return 503 until the
   host is changed. Core platform unaffected.
2. ⚠️ **Raster analytics functionally unverified.** They cannot be exercised
   here, so whether they *work* once rasterio loads is untested — only their
   failure path is proven.
3. ⚠️ **Grey styling branch unexercised** — no uncategorised features exist.
4. 🚧 **No self-captured screenshots.** The browser pane cannot be displayed from
   the agent side; visual proof depends on user-supplied screenshots.
5. ⚠️ **`.env.example` documents `API_CORS_ORIGINS`**, but `config.py` reads
   `ALLOWED_ORIGINS`. Stale and misleading; not changed, as it is not a blocker.
6. ⚠️ **`.env` is gitignored**, so the CORS fix is local only. Another checkout
   on port 5273 will hit the same wall until its own `.env` is updated.

---

## 15. Baseline hardening pass

A second pass focused on configuration reproducibility. No architecture changed.

### 15.1 CORS naming inconsistency — resolved ✅

**Canonical variable: `ALLOWED_ORIGINS`.** It is declared in
`src/core/config.py`, read by pydantic-settings, and applied by `CORSMiddleware`
in `src/main.py`. Nothing else configures CORS.

The inconsistency was worse than a rename:

| Problem | Evidence | Status |
| --- | --- | --- |
| `.env.example` documented `API_CORS_ORIGINS` | Referenced **nowhere** in the codebase | fixed ✅ |
| `Settings` uses `extra="ignore"` | An unknown key is silently dropped, so setting `API_CORS_ORIGINS` fails **quietly** | documented ✅ |
| `apps/backend/.env.example` did not exist | The backend's real config file had no example at all | created ✅ |
| Default was `["http://localhost:3000"]` | Port 3000 belonged to the deleted Next.js scaffold; matches nothing | corrected ✅ |

Two runtime-verified gotchas, now documented:

```
ALLOWED_ORIGINS=http://a,http://b   ->  REJECTED (SettingsError)
ALLOWED_ORIGINS='["http://a"]'      ->  ['http://a']
```

`list[str]` is parsed as JSON, so a comma-separated value raises `SettingsError`.

```
Settings() from repo root     ->  DATABASE_URL loaded: False, CORS: default
Settings() from apps/backend  ->  DATABASE_URL loaded: True,  CORS: from .env
```

`env_file=".env"` resolves against the **current working directory**. Started
from the wrong directory, the backend silently runs on defaults.

Validation — `.env.example` was loaded through `Settings` to prove it works,
rather than assumed: ✅

```
DATABASE_URL    : postgresql+asyncpg://terramind:terramind_local@localhost:5432/terramind_db
REDIS_URL       : redis://localhost:6379/0
SECRET_KEY set  : True
ALLOWED_ORIGINS : ['http://localhost:5273', 'http://127.0.0.1:5273']
```

No secrets committed: `SECRET_KEY=change-me` is a placeholder, and the Postgres
credentials are the local container defaults already present in
`docker-compose.yml`.

### 15.2 Frontend environment reproducibility — resolved ✅

The frontend reads exactly one variable, `VITE_API_BASE_URL`
(`import.meta.env.DEV` is a Vite built-in and needs no configuration). No new
variables were introduced.

`frontend/.env.example` was **wrong and would break a fresh checkout** — proven,
not suspected:

```
GET http://localhost:8000/projects         ->  404   (old example value)
GET http://127.0.0.1:8000/api/v1/projects  ->  200   (actual value)
```

The application appends paths directly to this base, so the missing `/api/v1`
suffix 404s every request. Corrected, with the suffix requirement and the
CORS-origin dependency both called out in the file.

### 15.3 Three environment files, now clearly separated ✅

| File | Consumer | Notes |
| --- | --- | --- |
| `.env.example` | docker-compose only | Only `POSTGRES_USER/PASSWORD/DB` are actually consumed |
| `apps/backend/.env.example` | FastAPI (pydantic-settings) | **CORS lives here** |
| `frontend/.env.example` | Vite | `VITE_API_BASE_URL` only |

Dead keys removed from the root example after confirming zero code references:
`API_ENV`, `API_CORS_ORIGINS`, `REDIS_HOST`, `REDIS_PORT`, `POSTGRES_HOST`,
`POSTGRES_PORT`.

### 15.4 Startup procedure — verified from a clean stop ✅

Full stop, then start via the documented command, observed end to end:

```
[1/5] Containers (db, redis)...   postgres ready
[2/5] Database migrations...      schema at head
[3/5] Celery worker...            worker launched
[4/5] FastAPI...                  api ready
[5/5] Vite dev server...          frontend ready
```

Celery registered both tasks on startup, confirming the explicit-import fix
still holds.

**Commands:**

```powershell
# whole stack
powershell -ExecutionPolicy Bypass -File scripts\start_stack.ps1
powershell -ExecutionPolicy Bypass -File scripts\stop_stack.ps1

# backend alone - MUST run from apps/backend so .env is found
cd apps\backend
$env:PYTHONPATH = (Get-Item .).FullName
.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000

# frontend alone
cd frontend
pnpm dev --port 5273 --strictPort

# dependencies (required first)
docker compose up -d db redis
```

---

## Current Baseline

### ✅ VERIFIED WORKING

| Capability | Evidence |
| --- | --- |
| Backend boots | uvicorn alive, no traceback, `Application startup complete` |
| Health endpoint | `GET /api/v1/health` → 200 |
| Readiness (Postgres + Redis) | `GET /api/v1/ready` → 200, both up |
| Project API | `GET /projects` → 200, 3 projects |
| Dataset listing | `GET /projects/{id}/datasets` → 200, 4 datasets |
| Dataset retrieval | `.../geojson` → 200, **1,188 features** |
| Spatial query — contains | `ST_Contains` → 1 feature |
| Spatial query — nearby | `ST_DWithin` → 74 features |
| Celery task registration | both tasks listed under `[tasks]` |
| Raster endpoints degrade cleanly | `POST /analysis`, `/geospatial/vectorize` → 503, actionable message |
| Vector endpoints independent of rasterio | all 200 while rasterio is unloadable |
| Frontend ↔ backend | 5 browser requests, all 200, cross-origin from 5273 |
| Map renders | canvas 1296×874, `engineState = ready`, 93 style layers |
| Dataset layers | fill / line / circle created |
| Feature integrity | 1,188 source features, **0 invalid geometries**, valid WGS-84 |
| Features rendered | **1,179** at z11.22 |
| Styling applied | park `rgba(230,159,0)`, hospital `rgba(86,180,233)`, station `rgba(0,158,115)` |
| Legend | park / hospital / station |
| Zoom | z13 → 198 features; z9.5 → 779; bounds change correctly |
| Pan | centre `77.5046,12.9004 → 77.6284,12.8257`; 1,179 → 698 features |
| No infinite loading | overlay cleared |
| No console errors | zero |
| Quality gates | 6/6 pass |
| Config reproducibility | `.env.example` loads through `Settings` |

### 🚧 ENVIRONMENT BLOCKED

| Item | Detail |
| --- | --- |
| rasterio native extension | Smart App Control blocks `_base.cp313-win_amd64.pyd`. Not a repo defect; SAC has no exclusion mechanism. Fix requires disabling SAC (irreversible), Docker/WSL, or a trusted build. |
| Raster analytics | Unavailable while the above holds. Fails at 503, never at import. |
| Agent-side screenshots | The automated browser pane never composites here; visual proof depends on user-supplied screenshots. |

### ⚠️ NOT IMPLEMENTED YET / NOT VERIFIED

| Item | Detail |
| --- | --- |
| Phase 5 — AI / NL query | Deliberately untouched. No LLM, parser, chat UI or agentic reasoning. |
| Raster analytics behaviour | Only the failure path is proven; correct operation is untested here. |
| Grey styling fallback | All 1,188 features carry a category, so the default branch is never taken. |
| Dataset DELETE endpoint | Absent; `removeDataset` is a client-side no-op with a notification. |
| Prettier gate | 146 files unformatted; not enforced in CI. |
| `.env` files | gitignored, so each checkout must copy the examples. |

### Observation, not a blocker

Floating workspace panels can overlap. With the Datasets panel open over the
Projects panel, clicks intended for a project card land on the Datasets panel
instead. Reproduced during this pass; closing the covering panel resolves it.
Cosmetic/UX only — it does not affect the data pipeline.

---

## Running services (left up)

| Service | URL | State |
| --- | --- | --- |
| Backend (FastAPI) | http://127.0.0.1:8000 | running |
| API docs | http://127.0.0.1:8000/docs | running |
| Frontend (Vite) | http://localhost:5273 | running |
| Postgres/PostGIS | localhost:5432 | container up |
| Redis | localhost:6379 | container up |
| Celery worker | — | running (`--pool=solo`) |

---

## Recommended starting point for Phase 5

The vector pipeline is a reliable foundation. Phase 5 should build on it as
follows. **Nothing below has been started.**

**Start here — a backend endpoint, not a frontend chat box:**

```
POST /api/v1/projects/{project_id}/query/natural
  { "query": "hospitals within 2km of Lalbagh" }
    -> translate to an existing spatial primitive
    -> ST_DWithin / ST_Contains / ST_Intersects
    -> return the SAME FeatureCollection shape already rendered
```

Why this is the right seam:

1. **The output contract already works.** Every spatial endpoint returns a
   `FeatureCollection` the map already renders and styles. If Phase 5 emits that
   same shape, no rendering work is required.
2. **The primitives exist and are verified** — `query/nearby`, `query/contains`,
   `query/intersects`. The model's job is to choose one and fill its parameters,
   not to invent spatial analysis.
3. **Keep the model out of SQL.** Have it emit a constrained, validated
   structure (predicate + dataset + parameters) that the backend maps onto
   existing repository methods. That is testable without a live model and avoids
   injection risk.
4. **`src/ai/` already has provider/registry/service scaffolding** used for
   SegFormer; the NL layer should sit alongside it rather than replace it.

**Blocking decision before any code:** which LLM provider, and where the API key
lives. That is a product decision, not a technical one.

**Do not start with** a chat UI, agentic multi-step reasoning, or letting a model
generate raw SQL/PostGIS. Prove single-predicate translation end to end first.
