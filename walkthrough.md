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

## 16. Styling fallback verification (temporary fixture)

Previously recorded as ⚠️ unverified: every feature in `bangalore osm` carries a
`category`, so the grey default branch was never exercised. This closes that gap.

**No production styling logic was changed, and grey is not hardcoded anywhere in
the rendering layer** — the fallback is produced by `buildCategoricalStyle`'s
`defaultStyle` and emitted as the final branch of the compiled `case`
expression.

### Method

A temporary dataset was uploaded through the real API (`POST
/projects/{id}/datasets`) and rendered through the real UI. 9 polygons in three
columns:

| Column | Longitude | `category` property |
| --- | --- | --- |
| 3 features | 77.40 | `"park"` |
| 3 features | 77.44 | `"hospital"` |
| 3 features | 77.48 | **absent** |

A feature with no `category` matches no equality rule, so it must fall through
to the default branch.

### Result — ✅ the grey fallback works

The compiled expression contained **two** rules only; the uncategorised features
produced none:

```json
rulesInOrder: [
  { "category": "hospital", "colour": "rgba(230, 159, 0, 1.000)" },
  { "category": "park",     "colour": "rgba(86, 180, 233, 1.000)" }
]
defaultBranch: "rgba(120, 120, 120, 1.000)"
```

The legend showed only `hospital` and `park`.

Configuration alone is not proof, so rendered pixels were sampled from the WebGL
framebuffer over each column:

| Sample | Observed | Channel spread | Reading |
| --- | --- | --- | --- |
| hospital, x=77.449 | `rgb(91,68,13)` | 78 | warm — rule 1 |
| park, x=77.409 | `rgb(39,72,91)` | 52 | cool — rule 2 |
| **uncategorised, x=77.489** | **`rgb(54,54,54)`** | **0** | **neutral grey** |
| **uncategorised, x=77.489 (2nd)** | **`rgb(54,54,55)`** | **1** | **neutral grey** |
| basemap control, no feature | `rgb(14,14,14)` | 0 | dark basemap |

The uncategorised samples are **neutral (spread ≈ 0) and brighter than the
basemap control**, so a grey fill is genuinely being drawn rather than the
basemap showing through. The arithmetic agrees: `fill-opacity` is 0.4, so
`0.4 × 120 + 0.6 × 14 = 56`, against 54 observed.

### Incidental finding — palette assignment is rank-based, not semantic

The fixture gave `park` and `hospital` an equal count of 3.
`summariseCategories` sorts by count descending and breaks ties with
`localeCompare`, so `hospital` sorted first and took palette slot 0 (orange),
while `park` took slot 1 (blue) — the reverse of their colours on the OSM
dataset.

This is correct, documented behaviour, not a defect: colours are assigned by
**frequency rank**, not by category meaning. It does mean the shorthand
"parks → orange, hospitals → blue" holds for `bangalore osm` only because parks
(672) outnumber hospitals (473). A different dataset will assign different
colours to the same names.

Worth knowing before anyone treats those colours as fixed, or writes a test that
assumes them.

### Cleanup — ✅ fixture removed

```
before delete : datasets=1  features=9
DELETE 1
after delete  : datasets=0  features=0
API           : 4 datasets, fixture present: False
```

The dataset row was deleted directly in Postgres, cascading to its features,
because the backend has no DELETE endpoint (see the open items). The fixture
file itself was written to a scratch directory outside the repository, so
`git status` was unaffected throughout.

---

## 17. Backend in Docker — rasterio blocker resolved ✅

The Smart App Control blocker (§3) is a **host policy**, so it does not apply
inside a Linux container. The backend now runs in Docker with rasterio working.

### Files added

| File | Purpose |
| --- | --- |
| `docker/Dockerfile.backend` | `python:3.13-slim`; shared by the API and the Celery worker |
| `.dockerignore` | Keeps `.venv`, `node_modules` and **`.env`** out of the build context |
| `docker-compose.yml` | `backend` + `celery_worker` services added; healthchecks on `db`/`redis` |

### Two real defects this exposed

Both were pre-existing repository bugs that only surfaced in a clean environment.

**1. `libexpat1` is required — my initial assessment was wrong.**

The first inspection concluded that no system packages were needed, because
rasterio's manylinux wheel bundles GDAL and declares no GDAL dependency. That is
true but incomplete: the bundled GDAL still links against the system
`libexpat.so.1`, which `python:3.13-slim` omits.

```
ImportError: libexpat.so.1: cannot open shared object file
```

Rather than guess packages, `ldd` was run over every `.so` in `rasterio` and
`rasterio.libs`. Exactly one dependency was unresolved:

```
missing across rasterio + bundled libs : libexpat.so.1
missing across pyproj / shapely        : (none - RPATH-resolved at runtime)
```

`libexpat1` alone fixes it. **No `libgdal-dev` is needed**, which keeps the
image ~300MB smaller and avoids a version clash with the bundled GDAL 3.12.4.

**2. `python-multipart` was missing from `requirements.txt`.**

The container crash-looped on startup:

```
RuntimeError: Form data requires "python-multipart" to be installed.
```

The dataset upload endpoint uses `UploadFile`, which needs it. It was installed
in the host venv — which is why uploads always worked locally — but never
pinned. Comparing `pip freeze` against `requirements.txt` showed it was the only
drift:

```
python-multipart==0.0.32
```

Now pinned; the freeze and the requirements file are identical again.

### Verification — ✅

Inside the running API container:

```
rasterio 1.5.1 | bundled GDAL 3.12.4
get_raster_provider() -> COGRasterProvider
get_polygonizer()     -> RasterPolygonizer
```

Those are the exact classes that are unimportable on the host.

The decisive comparison, same request against both:

| Environment | `POST /api/v1/analysis` | Meaning |
| --- | --- | --- |
| Host (native, SAC-blocked) | **503** | rasterio unavailable, dependency refused |
| Container | **422** | dependency resolved; request reached body validation |

422 is the expected response to the deliberately empty `{}` body. The word
"rasterio" no longer appears anywhere in the error. The same holds for
`POST /geospatial/vectorize`.

The vector pipeline is unaffected by the move — all endpoints served from the
container:

```
/health 200 · /ready 200 · /projects 200 (3) · /datasets 200 (4)
/geojson 200 (1188 features) · contains 200 (1) · nearby 200 (74)
POST /datasets (multipart) 201   <- python-multipart fix confirmed
```

Celery worker in-container:

```
[tasks]
  . src.async_processing.tasks.ai_tasks.run_ai_inference_task
  . src.async_processing.tasks.geospatial_tasks.run_geospatial_vectorization_task
Connected to redis://redis:6379/0
celery@39b999c9b55b ready.
```

CORS from the host browser origin to the containerised API:

```
OPTIONS /projects (Origin: http://localhost:5273) -> 200
access-control-allow-origin: http://localhost:5273
```

All four containers report healthy.

### Design notes

- **No system GDAL/PROJ/GEOS.** Only `libexpat1` (rasterio) and `curl` (healthcheck).
- **`.env` is excluded** from the build context, so local config and `SECRET_KEY`
  are never baked into the image. Configuration comes from compose `environment:`,
  which takes precedence over the `.env` file anyway.
- **Container hostnames** — `@db:5432`, `redis://redis:6379`, not `localhost`.
- **`--pool=solo` deliberately dropped** for the worker: that is a Windows-only
  workaround for billiard permission errors and is unnecessary on Linux.
- **Healthchecks** on `db`/`redis` with `depends_on: condition: service_healthy`,
  so the backend cannot start against a database still initialising.
- **The worker overrides the image healthcheck.** It inherited the API's
  `curl /api/v1/health`, which it can never pass since it serves no HTTP; it was
  reporting `unhealthy` until replaced with `celery inspect ping`. The first
  version of that replacement was also wrong: a 15s timeout against a check that
  measures ~11s (of which ~4s is importing torch) produced intermittent false
  failures. Timings were re-set from the measured cost — `interval 60s`,
  `timeout 30s`, `start_period 90s` — and confirmed stable across several
  cycles. The worker itself was never unhealthy; the check was.
- **One shared image tag** (`terramind-backend:latest`) so the 2.13GB image is
  built once rather than per service.
- **Port 8000 collides** with the native backend from `scripts/start_stack.ps1`.
  Run one or the other, or set `BACKEND_PORT`.

### What this does and does not change

✅ Raster analytics can now run, in Docker.
🚧 The **host** environment is unchanged — running natively on Windows still
hits Smart App Control and still returns 503. That degradation path remains
correct and is still the right behaviour there.
✅ Raster analytics are reachable **and proven correct** — see the NDVI
fixture result below.

---

### Raster analytics proven end to end — ✅

The gap left open above ("reachable but not proven correct") is now closed. A
deterministic GeoTIFF was pushed through `POST /api/v1/analysis`.

`_resolve_bands` maps an index's required bands **positionally**, so NDVI's
`["NIR", "RED"]` means band 1 = NIR, band 2 = RED. The fixture was built to make
the answer predictable in advance:

| Region | NIR | RED | Expected NDVI |
| --- | --- | --- | --- |
| top half | 0.6 | 0.2 | `(0.6-0.2)/(0.6+0.2)` = **0.50** |
| bottom half | 0.3 | 0.3 | `0/0.6` = **0.00** |

100x100 float32, EPSG:4326, tiled+deflate, generated with rasterio inside the
running container.

**Result: HTTP 200, `processing_status: completed`,** and every statistic
matches the prediction:

| Statistic | Predicted | Returned |
| --- | --- | --- |
| min | 0.00 | `0.0` |
| max | 0.50 | `0.5000000596` |
| mean | 0.25 | `0.2500000298` |
| median | 0.25 | `0.2500000298` |
| variance | 0.0625 (= 0.25²) | `0.0625000075` |
| std_dev | 0.25 | `0.25` |
| valid_pixels | 10000 | `10000` |
| nodata_pixels | 0 | `0` |

Percentiles `p5=0.0, p25=0.0, p50=0.25, p75=0.5, p95=0.5` are exactly right for
a 50/50 bimodal split, and a histogram (`frequencies` + `bin_edges`) was
returned. Raster metadata round-tripped correctly: 100x100, EPSG:4326, 2 bands.
The trailing `...0596` is float32 precision, not error.

Error handling was checked too:

```
missing raster       -> 404
ndbi (in the enum, not registered) -> 400
```

**This proves the analytics pipeline computes correct results**, not merely that
the rasterio import resolves: raster open, band read, index computation and
statistics all ran and agreed with hand-calculated values.

Fixture removed afterwards; `/analysis` returns 404 for it again, and the
repository was untouched throughout.

✅ **NDWI is now verified** on its own GREEN/NIR fixture — see below. Note that
NDVI and NDWI are numerically indistinguishable by construction under positional
band mapping; that is proven rather than assumed.

---

### NDWI verified — ✅ (and a design limitation found)

The earlier note said NDWI was untested because it would return values identical
to NDVI. Investigating that properly turned it from a testing gap into a
**documented property of the code**.

#### Why NDVI and NDWI cannot be told apart by output

```
NDVI: required_bands ["NIR", "RED"]    compute (nir   - red)/(nir   + red)
NDWI: required_bands ["GREEN", "NIR"]  compute (green - nir)/(green + nir)
```

`_resolve_bands` maps required bands **positionally** — first required band to
raster band 1, second to band 2, ignoring the names entirely. Both indices are
therefore `(band1 - band2)/(band1 + band2)`, and are **numerically identical on
any 2-band raster**.

This was proven, not assumed. The same raster through both indices:

```
ndwi on green/NIR raster -> min -0.6  max 0.6  mean 0.0  std 0.4898979962
ndvi on green/NIR raster -> min -0.6  max 0.6  mean 0.0  std 0.4898979962
```

Byte-identical. No fixture can distinguish them, so "an independent NDWI test"
in the numeric sense is not achievable by construction.

⚠️ **The real risk this exposes:** band selection is positional and
index-agnostic, so a raster whose band order does not match the requested index
produces a confidently wrong answer with **no error**. Requesting NDWI on a
NIR/RED raster returns plausible numbers that mean nothing. Band names in the
raster are read for metadata but never used to select bands.

#### What was verified instead

NDWI was tested on a fixture authored with its own semantics — band 1 = GREEN,
band 2 = NIR — with three regions chosen to make the answer predictable and to
exercise **negative output**, which the NDVI fixture never did:

| Region (rows) | GREEN | NIR | Expected NDWI |
| --- | --- | --- | --- |
| water, top third | 0.40 | 0.10 | `(0.4-0.1)/(0.4+0.1)` = **+0.60** |
| neutral, middle | 0.25 | 0.25 | `0/0.5` = **0.00** |
| vegetation, bottom | 0.10 | 0.40 | `(0.1-0.4)/(0.1+0.4)` = **-0.60** |

120x120 float32, EPSG:4326. Result — HTTP 200, `completed`:

| Statistic | Predicted | Returned |
| --- | --- | --- |
| min | -0.60 | `-0.6000000238` |
| max | +0.60 | `0.6000000238` |
| mean | 0.00 | `0.0` |
| median | 0.00 | `0.0` |
| variance | 0.24 | `0.2400000393` |
| std_dev | 0.4899 (= √0.24) | `0.4898979962` |
| valid_pixels | 14400 | `14400` |
| nodata_pixels | 0 | `0` |

Percentiles `p5=-0.6, p25=-0.6, p50=0.0, p75=0.6, p95=0.6` are exactly right for
an even three-way split. Negative values and the `clip_output(-1, 1)` path are
now exercised.

#### Incidental finding — `area_of_interest` is silently ignored ⚠️

Windowed reads were attempted to confirm spatial orientation (does "north" map
to the water rows?). All four requests returned identical statistics over the
full 14,400 pixels:

```
full raster        min -0.6  max 0.6  mean 0.0  pixels 14400
NORTH third        min -0.6  max 0.6  mean 0.0  pixels 14400
SOUTH third        min -0.6  max 0.6  mean 0.0  pixels 14400
MIDDLE third       min -0.6  max 0.6  mean 0.0  pixels 14400
```

This is **not a bug** — `_resolve_window` is an explicit stub:

```python
# AOI-to-pixel-window conversion requires CRS projection which depends
# on the open raster transform. For this milestone we use None (full
# raster) and leave windowed AOI projection for the next phase.
return None
```

The code is honest internally, but the **API is not**: `area_of_interest` is
accepted, validated, and returns HTTP 200 with whole-raster statistics. A caller
has no way to know their AOI was discarded. Either the field should be rejected
until implemented, or the response should indicate the window actually used.

As a consequence, spatial orientation of the raster read remains ⚠️ unverified —
it cannot be checked until windowed reads exist.

Both raster fixtures were removed afterwards; `/analysis` returns 404 for each,
and the repository was untouched throughout.

---

## 18. Two silent-failure fixes before Phase 5 ✅

Both gaps found in §17 shared the same failure mode: the API accepted a request,
returned **HTTP 200**, and gave an answer that was quietly not what was asked
for. That is the worst possible behaviour for a natural-language query layer,
which would emit these parameters without a human checking the response.

### 18.1 `area_of_interest` was silently discarded — now implemented ✅

`_resolve_window` returned `None` unconditionally, so every AOI was validated
and then thrown away; callers received whole-raster statistics with no signal.

It now converts the bounding box to a pixel window using the raster's own affine
transform (inverse of a north-up affine: `col = (x - c)/a`, `row = (y - f)/e`),
clamps to the raster extent, and **raises rather than silently widening the read**
for cases it cannot honour:

| Case | Behaviour |
| --- | --- |
| Rotated/sheared transform (`b` or `d` non-zero) | 400 — not supported |
| Zero pixel size | 400 — cannot resolve |
| Raster CRS is not lon/lat | 400 — AOI reprojection not supported yet |
| AOI does not intersect the raster | 400 — `"area_of_interest does not intersect the raster extent."` |

The provider already honoured windows correctly (`read_band` builds a
`rasterio.windows.Window`), so this was the only missing link.

**Verified** against the 120x120 three-region NDWI fixture (4800 px per third):

| Request | Expected | Returned |
| --- | --- | --- |
| full raster | mean 0.0, 14400 px | `mean 0.0, 14400` |
| NORTH third (water) | uniform +0.6, 4800 px | `min 0.6 max 0.6 mean 0.6, 4800` |
| MIDDLE third (neutral) | uniform 0.0, 4800 px | `min 0.0 max 0.0 mean 0.0, 4800` |
| SOUTH third (vegetation) | uniform -0.6, 4800 px | `min -0.6 max -0.6 mean -0.6, 4800` |
| AOI outside extent | error | `400` |

Each third is internally uniform (min = max = mean), so the window is landing
exactly on the intended rows, not merely reading fewer pixels.

**This also closes the "raster spatial orientation unverified" item.** North maps
to the water rows as authored, so the geotransform, the row ordering and the
window arithmetic all agree.

### 18.2 Positional band mapping could return confidently wrong values — now rejected ✅

`_resolve_bands` mapped an index's required bands to raster bands **by position,
ignoring names**. Since NDVI and NDWI are both `(band1 - band2)/(band1 + band2)`,
requesting the wrong index for a raster produced plausible numbers and no error —
nothing downstream could detect it.

Two changes:

1. **`COGRasterProvider` now surfaces band descriptions.** It previously
   populated only `identifier`, `dtype` and `nodata_value`, discarding
   `ds.descriptions`, so the analysis layer had no names to match on even when
   the raster carried them.
2. **`_resolve_bands` prefers labels when present.** If the raster labels its
   bands, required bands are matched by name (case-insensitive, across `name`,
   `common_name`, `description`). If a required band is absent, it **raises
   instead of falling back to position**. Unlabelled rasters keep the previous
   positional behaviour, so nothing that worked before breaks.

**Verified:**

```
NDWI on GREEN/NIR raster  -> 200, correct statistics
NDVI on GREEN/NIR raster  -> 400
  "Raster labels its bands ['GREEN', 'NIR'], which does not provide ['RED']
   required by this index. Refusing to fall back to positional order, which
   would read the wrong bands and return plausible but incorrect values."
```

Before this change that same request returned **200 with statistics identical to
NDWI's**.

**Backwards compatibility checked:** a deliberately unlabelled 2-band raster
(NIR 0.6 / RED 0.2) still resolves positionally and returns `mean 0.5` as
before.

### Files changed

| File | Change |
| --- | --- |
| `src/services/analysis_service.py` | AOI → `PixelWindow` implemented; name-aware band resolution with positional fallback |
| `src/analytics/providers/cog_provider.py` | Surface `ds.descriptions` as `BandInfo.name` / `.description` |

All six quality gates pass. Fixtures removed afterwards.

### Still not supported (now explicit rather than silent)

⚠️ AOI **reprojection** — an AOI against a non-lon/lat raster is rejected with a
clear message rather than applied unprojected.
⚠️ Rotated/sheared rasters with an AOI — rejected.
⚠️ Rasters that are unlabelled **and** in a non-standard band order remain
undetectable; there is nothing to match against. Labelling bands is the only
defence, and is now rewarded.

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
| Grey styling fallback | Verified with a temporary fixture (§16): uncategorised features render `rgb(54,54,54)`, neutral and distinct from the basemap |
| Raster analytics (Docker) | NDVI over a deterministic fixture: mean 0.25, min 0.0, max 0.5, variance 0.0625 — all matching hand-calculated values (§17) |
| NDWI (Docker) | Own GREEN/NIR fixture: min -0.6, max +0.6, mean 0.0, variance 0.24, std 0.4899 — matching hand-calculated values, incl. negative output |
| `area_of_interest` windowing | Implemented (§18.1). Each third of a 3-region raster returns uniform values at exactly 4800 px; out-of-extent AOI returns 400 |
| Raster spatial orientation | Verified via windowed reads — north maps to the authored water rows |
| Band-name resolution | Implemented (§18.2). Mismatched index now returns 400 with an explanatory message instead of 200 with wrong values; unlabelled rasters still resolve positionally |

### 🚧 ENVIRONMENT BLOCKED

| Item | Detail |
| --- | --- |
| rasterio native extension | Smart App Control blocks `_base.cp313-win_amd64.pyd`. Not a repo defect; SAC has no exclusion mechanism. Fix requires disabling SAC (irreversible), Docker/WSL, or a trusted build. |
| Raster analytics (native host only) | Unavailable on Windows while SAC holds; fails at 503, never at import. **Resolved in Docker — see §17.** |
| Agent-side screenshots | The automated browser pane never composites here; visual proof depends on user-supplied screenshots. |

### ⚠️ NOT IMPLEMENTED YET / NOT VERIFIED

| Item | Detail |
| --- | --- |
| Phase 5 — AI / NL query | Deliberately untouched. No LLM, parser, chat UI or agentic reasoning. |
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
