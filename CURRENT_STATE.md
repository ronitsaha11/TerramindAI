# TerraMind AI — Current State / Handoff

**Generated:** 2026-08-28 · **Against:** `main` @ `3f5c92e`
**Purpose:** verified starting state for a fresh Claude Code session. This is
**not** the Phase 5 implementation prompt.

Everything below was checked against the repository or a running system at the
time of writing. Where something could not be verified, it says so.

**Status labels**

| Label | Meaning |
| --- | --- |
| ✅ VERIFIED | Directly tested, with evidence recorded |
| ⚠️ PARTIALLY VERIFIED | Some behaviour proven, gaps remain |
| ❓ UNVERIFIED | Code exists; no sufficient runtime evidence |
| ❌ BROKEN | Known not to work |
| ⏸️ DEPRIORITIZED | Deliberately not being pursued |

---

## 1. Project Overview

**TerraMind AI is an Earth Intelligence platform for working with real
geographic datasets on an interactive map.**

The problem it addresses: answering geographic questions today means knowing
GIS tooling — PostGIS predicates, projections, band semantics. TerraMind's goal
is to let a domain user ask the question in plain language and get a correct
answer rendered on a map, with the geographic computation done by a trusted
engine rather than by a language model.

**Intended users:** analysts and domain specialists who need spatial answers but
are not GIS engineers.

**What users should eventually be able to do:** upload or select geographic
datasets, ask questions like *"Show hospitals within 2 km of Lalbagh"*, and see
the answer as styled features on a map.

**Core objective:**

```
User: "Show hospitals within 2 km of Lalbagh."
        ↓  natural-language interpretation
        ↓  structured spatial query
        ↓  validation
        ↓  existing TerraMind spatial engine
        ↓  Dataset Registry
        ↓  PostGIS / raster processing
        ↓  GeoJSON
        ↓  existing map
User sees the geographic result.
```

Today the pipeline works from *structured query* onward. The natural-language
front half does not exist yet — that is Phase 5.

**This is not a 3D globe project.** An earlier direction pursued planetary
rendering and was deliberately archived. See §6 and §13.

---

## 2. Current Development Status

| Area | Status |
| --- | --- |
| Backend boot, health, readiness | ✅ VERIFIED |
| PostgreSQL + PostGIS storage | ✅ VERIFIED |
| Redis + Celery worker | ✅ VERIFIED |
| Dataset registry (upload → store → retrieve) | ✅ VERIFIED |
| Vector spatial queries (nearby / contains / intersects) | ✅ VERIFIED |
| 2D map rendering of real features | ✅ VERIFIED (visual proof from user screenshots, see §5) |
| Attribute-based styling incl. grey fallback | ✅ VERIFIED |
| Raster analytics (NDVI, NDWI, statistics) **in Docker** | ✅ VERIFIED |
| Raster analytics **on native Windows host** | ❌ BROKEN (environment — §6.1) |
| AOI windowing, band-label validation | ✅ VERIFIED |
| Backend test suite | ⚠️ PARTIALLY VERIFIED — 2 failures, and CI does not run it (§6.7) |
| AI / CV inference (SegFormer) | ❓ UNVERIFIED end-to-end (§3, §5) |
| Natural-language query layer (Phase 5) | ❌ DOES NOT EXIST — no LLM code in the repository |
| Living Earth / 3D globe | ⏸️ DEPRIORITIZED — on an archive branch, not on `main` (§6.8) |
| Prettier formatting gate | ⏸️ DEPRIORITIZED (§6.9) |

---

## 3. Actual Architecture

### Frontend

- **Framework:** React 19 + TypeScript, **Vite 8** build tool
- **Map:** **MapLibre GL 6** — this is the live rendering path
- **Also present:** deck.gl 9 (`@deck.gl/*`) — legacy path, still backs a
  separate "Layers" panel. ⚠️ Two rendering systems coexist; check which one a
  change affects before editing.
- **State:** Zustand stores; **TanStack Query** for server state
- **API:** plain `fetch`, base URL from `VITE_API_BASE_URL`
- **Dev port:** **5273** (moved off 5173, which is used by another project on the
  development machine)

Key directories under `frontend/src/`:

```
core/datasets/     dataset contracts, importers, registry, rendering, validation
core/styles/       DatasetStyle / StyleRule / FeatureStyle + StyleEvaluator
features/earth/    EarthEngine, MapLibreDatasetRenderer, stores
features/datasets/ dataset panels + query panels
features/spatial/  spatial query UI
features/rendering/ deck.gl bridges (contains .bak files)
stores/            useProjectStore, workspace stores
```

### Backend

- **Framework:** FastAPI, entry `apps/backend/src/main.py`, `app = create_app()`
- **Python 3.13** (venv, CI, mypy target all 3.13; `requires-python = ">=3.11"`
  and `ruff target-version = py311` are looser and inconsistent)
- **Config:** pydantic-settings, `src/core/config.py`.
  ⚠️ `env_file=".env"` is **cwd-relative** — the backend must start from
  `apps/backend` or it silently runs on defaults.
- **Validation:** Pydantic models throughout; `AppException` + handlers in
  `src/core/exceptions.py`; responses wrapped in `SuccessResponse`

Modules under `apps/backend/src/`:

```
api/          v1 routers + dependencies (DI wiring)
analytics/    raster analysis: indices (NDVI/NDWI), statistics, COG provider
ai/           computer-vision inference (SegFormer) — NOT an LLM layer
geospatial/   polygonizer, geometry processor, GeoJSON exporter, service
repositories/ data access incl. dataset_repository (raw PostGIS SQL)
services/     dataset_service, analysis_service, project_service …
db/models/    SQLAlchemy models
async_processing/ Celery app, tasks, worker
```

### Database — ✅ VERIFIED

- **PostgreSQL 15 + PostGIS 3.3** (`postgis/postgis:15-3.3` container)
- SQLAlchemy **async** + asyncpg
- Tables include `projects`, `datasets`, `dataset_features`, `regions`, `jobs`,
  `users`, `predictions`, `audit_logs`
- `dataset_features.geometry` is a real PostGIS `Geometry` column with a **GiST
  index**
- Timestamps are `DateTime(timezone=True)` via the declarative type annotation
  map — a naive/aware mismatch previously crashed asyncpg
- **Migrations:** Alembic, 3 revisions, currently at head `a90513d23268`

### Redis — ✅ VERIFIED

Celery broker (`/0`) and result backend (`/1`); also checked by `/api/v1/ready`.
`redis:alpine` container.

### Celery — ✅ VERIFIED (worker starts, registers tasks)

Two tasks registered: `run_ai_inference_task`, `run_geospatial_vectorization_task`.

⚠️ **Task registration uses explicit imports, not autodiscovery.**
`autodiscover_tasks` did not actually import the task modules, so FastAPI's
enqueue failed with "task not registered" while the worker looked healthy. The
imports in `celery_app.py` carry `# noqa: E402, F401` — **`ruff --fix` will
delete them and silently reintroduce the bug.**

❓ **No task has been executed end-to-end.** Registration is verified; running a
job through the queue is not.

### Dataset Registry — ✅ VERIFIED

- Upload: `POST /api/v1/projects/{project_id}/datasets` (multipart GeoJSON)
- `DatasetService.create_dataset_from_geojson` parses with shapely, computes
  metadata **from the file** (`feature_count`, `geometry_type`, `extent`,
  attribute types), and persists geometries as `SRID=4326` EWKT
- Retrieval: `GET .../datasets` and `.../datasets/{id}/geojson`
- The spatial engine reads through `DatasetFeatureRepository` (raw SQL against
  `dataset_features`)
- ❌ **No DELETE endpoint exists.** `removeDataset` in the frontend is a
  client-side no-op with a notification; test fixtures were removed via `psql`.

### Spatial Engine — ✅ VERIFIED (vector)

Implemented in `src/repositories/dataset_repository.py`:

| Operation | Predicate |
| --- | --- |
| nearby | `ST_DWithin` — **both sides cast to `::geography`** so radius is metres, not degrees |
| contains | `ST_Contains` from a clicked polygon |
| intersects | `ST_Intersects` against a second dataset |

Contains and intersects exclude the source feature so a dataset compared with
itself does not trivially match.

Raster side: `src/analytics/` (indices, statistics, `COGRasterProvider`) and
`src/geospatial/` (`RasterPolygonizer`, geometry processing, GeoJSON export).

### Vector Pipeline — ✅ VERIFIED end-to-end

```
GeoJSON upload → shapely validation → PostGIS geometry + GiST index
  → repository SQL (ST_DWithin / ST_Contains / ST_Intersects)
  → FeatureCollection → frontend fetch → MapLibre GeoJSON source
  → fill / line / circle layers → rendered features
```

### Raster Pipeline — ✅ VERIFIED in Docker

```
GeoTIFF/COG → COGRasterProvider (rasterio + bundled GDAL 3.12.4)
  → band resolution (label-aware, positional fallback)
  → optional AOI → PixelWindow (affine inverse)
  → index computation (NDVI / NDWI)
  → StatisticsEngine (min/max/mean/median/variance/std, histogram, percentiles)
  → AnalysisResult
```

`RasterPolygonizer` (raster → vector) exists and imports, but ❓ has not been
exercised end-to-end.

### Rendering / Map

- **`MapLibreDatasetRenderer`** (`features/earth/services/`) is the live path —
  adds a GeoJSON source per dataset plus `dataset-fill-*`, `dataset-line-*`,
  `dataset-circle-*` layers filtered by `$type`, and cleans up on toggle-off.
- Spatial query results render as separate, colour-distinct layers (nearby
  yellow/orange, contains violet/green, intersects rose/cyan).
- **Styling:** `core/styles` types (`DatasetStyle`, `StyleRule`, `FeatureStyle`)
  are **compiled into MapLibre `case` expressions** by
  `style-expression-compiler.ts`, so rules evaluate on the GPU rather than per
  feature in JS. `StyleEvaluator` still exists for the deck.gl path.
- ⚠️ **MapLibre discards non-numeric feature ids.** The backend's UUIDs are
  mirrored into `properties.__feature_id` so click hit-testing works. Removing
  that breaks all click-to-query interaction.

### AI Infrastructure — ❗ read carefully

**`apps/backend/src/ai/` is computer-vision inference, not an LLM layer.**

It wraps **SegFormer** (HuggingFace Transformers + PyTorch) for semantic
segmentation of rasters, feeding `RasterPolygonizer` to turn masks into
polygons. Files: `base.py`, `loader.py`, `manager.py`, `models.py`, `registry.py`,
`service.py`, `providers/segformer.py`, `processing/{pre,post}processor.py`.
Route: `POST /api/v1/ai/inference`.

**There is no LLM code anywhere in the repository.** A repo-wide search for
`anthropic|openai|claude|langchain|gpt-` returns no source matches. Phase 5
starts from zero on that front — but the provider/registry/service *pattern* in
`src/ai/` is a reasonable shape to mirror.

❓ SegFormer inference was reported working on a dummy 512×512 input in an
earlier session; it has **not** been re-verified here, and is not wired to the
frontend or the dataset pipeline.

### Docker — ✅ VERIFIED

- `docker/Dockerfile.backend` — `python:3.13-slim`, shared by API and worker
- `docker-compose.yml` — `db`, `redis`, `backend`, `celery_worker`
- `.dockerignore` — excludes `.env`, `.venv`, `node_modules`
- Image ~2.13 GB (torch dominates); one shared tag `terramind-backend:latest`
- Healthchecks on all four services
- **`libexpat1` is required** — see §7.2
- The frontend is deliberately **not** containerised (runs on host for HMR)

---

## 4. Architecture Diagram

### What exists today (verified)

```
                        USER
                          │
                          ▼
              FRONTEND (Vite + React, :5273)
                MapLibre GL  ·  Zustand  ·  TanStack Query
                          │  fetch, VITE_API_BASE_URL
                          ▼
              BACKEND API (FastAPI, :8000)
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
     DATASET REGISTRY            ANALYTICS / GEOSPATIAL
     DatasetService              AnalysisService
     DatasetRepository           COGRasterProvider
            │                           │
            └─────────────┬─────────────┘
                          ▼
                   SPATIAL ENGINE
            ┌─────────────┴─────────────┐
            ▼                           ▼
   PostgreSQL + PostGIS         rasterio + bundled GDAL
   ST_DWithin / ST_Contains     NDVI · NDWI · statistics
   ST_Intersects  (GiST)        (Docker only — see §6.1)
            │                           │
            └─────────────┬─────────────┘
                          ▼
                       GeoJSON
                          ▼
                    MAP (MapLibre)

   Redis ──► Celery worker (tasks registered; ❓ none executed end-to-end)
```

### Phase 5 — **PLANNED / NOT YET IMPLEMENTED**

No code for this path exists.

```
USER NATURAL LANGUAGE
        │
        ▼
   CLAUDE API              ← does not exist yet
        │
        ▼
STRUCTURED SPATIAL QUERY   ← does not exist yet
        │
        ▼
   VALIDATION              ← does not exist yet
        │
        ▼
EXISTING SPATIAL ENGINE    ← exists and is verified
```

---

## 5. Verified Working Features

### Backend

| Feature | Status | Evidence | Endpoint / file |
| --- | --- | --- | --- |
| API startup | ✅ | `Application startup complete`, no traceback | `src/main.py` |
| Health | ✅ | 200 | `GET /api/v1/health` |
| Readiness (PG + Redis) | ✅ | 200, both reported up | `GET /api/v1/ready` |
| PostgreSQL | ✅ | queries return real rows | `src/db/session.py` |
| Redis | ✅ | `Redis client connected` | `src/core/redis.py` |
| Celery | ✅ registration / ❓ execution | both tasks under `[tasks]`, `celery@… ready` | `src/async_processing/` |
| CORS | ✅ | preflight 200, `access-control-allow-origin: http://localhost:5273` | `src/main.py` |
| Projects API | ✅ | 3 projects returned | `GET /api/v1/projects` |
| Dataset API | ✅ | 4 datasets; upload returns 201 | `.../projects/{id}/datasets` |

28 routes in the OpenAPI schema.

### Vector Data — ✅ VERIFIED with measured values

Measured against dataset `bangalore osm`
(`86366ad9-9947-4096-a7db-44be16050193`):

```
Dataset features        : 1,188   (672 parks, 473 hospitals, 43 stations)
Rendered features       : 1,179   at zoom 11.22
Invalid geometries      : 0
CRS                     : WGS-84 lon/lat; footer reports EPSG:4326
Data bounds             : [77.4088, 12.8002, 77.6004, 13.0004]
Viewport bounds         : [77.28, 12.78 → 77.67, 13.03]  (data inside viewport)
Canvas                  : 1296 × 874
Layer visibility        : visible; opacity fill 0.4, line 1, circle 1
```

Spatial queries, each cross-checked against raw SQL run directly on PostGIS:

| Query | Result |
| --- | --- |
| contains — "Bangalore Central" | exactly "City Center" (1 feature) |
| contains — Lalbagh Botanical Gardens | exactly "Fossilized Tree" (1 feature) |
| nearby — 2 km of 77.55/12.95 | 74 features |
| intersects — ward × OSM dataset | 875 features (420 hospitals / 424 parks / 31 stations) |

Viewport behaviour:

```
zoom 13   → 198 rendered features
zoom 9.5  → 779 rendered features
pan       → centre 77.5046,12.9004 → 77.6284,12.8257; 1,179 → 698 features
```

Styling — compiled MapLibre expression observed on the live map:

```
park     rgba(230,159,0)    hospital rgba(86,180,233)
station  rgba(0,158,115)    default  rgba(120,120,120)
```

⚠️ **Colours are assigned by frequency rank, not by category meaning.**
`park → orange` holds for this dataset only because parks are most numerous.
A different dataset will assign different colours to the same names. Do not
write tests that assume these colours.

**Grey fallback — ✅ VERIFIED** (it was previously only assumed). A temporary
9-feature fixture with three uncategorised features produced a 2-rule expression,
and pixel sampling over the uncategorised polygons returned `rgb(54,54,54)`
(neutral, spread 0) against a basemap control of `rgb(14,14,14)` — a grey fill is
genuinely drawn. Fixture removed afterwards.

### Raster — ✅ VERIFIED in Docker

| Item | Status | Evidence |
| --- | --- | --- |
| rasterio | ✅ in container / ❌ on host | `1.5.1`, bundled GDAL `3.12.4` |
| GDAL | ✅ | bundled in the manylinux wheel; no system GDAL installed |
| COGRasterProvider | ✅ | instantiates; opens and reads real GeoTIFFs |
| RasterPolygonizer | ⚠️ | class instantiates; ❓ never exercised end-to-end |
| NDVI | ✅ | see below |
| NDWI | ✅ | see below |
| Statistics | ✅ | histogram, percentiles, variance all correct |
| AOI / windowing | ✅ | see below |
| Band-label validation | ✅ | mismatched index rejected with 400 |
| Positional fallback | ✅ | unlabelled raster still resolves, `mean 0.5` |
| Error handling | ✅ | missing raster 404; unregistered index 400 |

**NDVI** — deterministic fixture (top half NIR .6/RED .2 → 0.5; bottom half
NIR .3/RED .3 → 0.0). Every value predicted before running:

```
min 0.0            max 0.5000000596    mean 0.2500000298
median 0.2500000298  variance 0.0625    std_dev 0.25
valid_pixels 10000   nodata_pixels 0
percentiles p5 0.0, p25 0.0, p50 0.25, p75 0.5, p95 0.5
```

**NDWI** — own GREEN/NIR fixture exercising negative output:

```
min -0.6000000238  max 0.6000000238   mean 0.0   median 0.0
variance 0.2400000393   std_dev 0.4898979962   valid_pixels 14400
```

**AOI windowing** — each third of a three-region raster returns *uniform* values
at exactly 4800 of 14400 pixels, which also confirms spatial orientation:

```
full raster   mean  0.0   14400 px
NORTH third   min  0.6  max  0.6  mean  0.6   4800 px
MIDDLE third  min  0.0  max  0.0  mean  0.0   4800 px
SOUTH third   min -0.6  max -0.6  mean -0.6   4800 px
AOI outside extent → 400
```

⚠️ **NDVI and NDWI are numerically indistinguishable on any 2-band raster** —
both reduce to `(band1 − band2)/(band1 + band2)`. Proven: the same raster through
both indices returned byte-identical statistics. Correctness therefore depends on
band **labels**, which is why label validation exists.

### Frontend

| Item | Status | Notes |
| --- | --- | --- |
| Dev server port | ✅ | **5273** (not 5173) |
| API connectivity | ✅ | 5 browser requests, all 200, cross-origin |
| Map rendering | ✅ | see below on how this was verified |
| Feature styling | ✅ | orange/blue/green visible |
| Pan / zoom | ✅ | measured, §5 Vector Data |
| Feature updates on viewport change | ✅ | counts change with zoom/pan |
| Console errors | ✅ | zero |
| Telemetry | ⏸️ | belongs to the archived Living Earth work; not on `main` |

❗ **How visual verification was obtained.** The automated browser pane in the
previous session never composited frames, so screenshots timed out and the agent
**could not capture the map itself**. Visual confirmation came from
**screenshots supplied by the user**, showing the 2D map with orange parks, blue
hospitals and green stations over Bengaluru at `localhost:5273`. Everything else
was verified programmatically against the live map instance. A future session
should re-confirm visually rather than treat this as agent-observed.

⚠️ Because the pane was hidden, MapLibre's `requestAnimationFrame` loop was
paused; render passes had to be driven manually for automated checks. That is a
**harness workaround, not application behaviour** — in a normal browser the map
initialises on its own.

---

## 6. Known Bugs and Limitations

### 6.1 Native Windows rasterio — ❌ BROKEN (environment)

```
Issue:      rasterio cannot load on the Windows host
Symptom:    ImportError: DLL load failed while importing _base:
            An Application Control policy has blocked this file.
Root Cause: Windows Smart App Control is ON and enforcing, blocking
            rasterio's unsigned bundled GDAL extension. Verified via
            HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy →
            VerifiedAndReputablePolicyState = 1. Only rasterio is affected;
            numpy, shapely, asyncpg, pyproj and torch all import fine.
            A clean install of the latest version is blocked identically.
Status:     Isolated, not repaired. Raster endpoints return 503 natively.
Impact:     Raster analytics unavailable when running the backend natively.
            Vector/dataset/spatial endpoints unaffected.
Blocks P5?: NO — Phase 5 targets vector queries.
Solution:   Run the backend in Docker (works today), or disable Smart App
            Control (IRREVERSIBLE — cannot be re-enabled without reinstalling
            Windows). SAC has no exclusion mechanism.
```

### 6.2 Raster limitations — ⚠️ explicit, not silent

All now return 400 with a clear message rather than a wrong answer:

- **AOI reprojection** not supported — AOI must be lon/lat and the raster CRS
  must be EPSG:4326 / OGC:CRS84
- **Rotated or sheared rasters** with an AOI — rejected
- **Unlabelled rasters** in non-standard band order remain **undetectable**;
  there is nothing to match against. Labelling bands is the only defence.

### 6.3 No dataset DELETE endpoint — ⚠️

`removeDataset` is a client-side no-op showing "not yet implemented". Test
fixtures had to be deleted with `psql`. Three duplicate `test data` datasets
remain in the database.

### 6.4 Two rendering systems coexist — ⚠️

deck.gl `LayerManager` (Layers panel) and `MapLibreDatasetRenderer` (Datasets
panel + spatial queries). Editing the wrong one produces no visible effect.
`features/rendering/bridges/` contains `.bak` files from the archived globe work.

### 6.5 Overlapping panels intercept clicks — ⚠️ cosmetic

With the Datasets panel open over the Projects panel, clicks aimed at a project
card land on the Datasets panel. Reproduced; closing the covering panel resolves
it. Does not affect the data pipeline.

### 6.6 `env_file` is cwd-relative — ⚠️

Starting the backend from the repository root silently loads **no** config
(`DATABASE_URL` empty, CORS falls back to defaults). It must be started from
`apps/backend`. Documented in `apps/backend/.env.example`.

### 6.7 Test suite: 2 failures, and CI never runs it — ❌

**43 test files exist** (`apps/backend/tests/`). `pytest` is **commented out** in
`.github/workflows/ci.yml`, so these have not been gating anything.

Running the suite now: **2 failures**, ~146 passing.

```
FAILED tests/unit/async_processing/test_celery_app.py::test_autodiscovery_enabled
FAILED tests/unit/test_initial_migration.py::
       test_initial_migration_declares_every_current_model_table
```

1. **`test_autodiscovery_enabled`** asserts
   `autodiscover_tasks(["src.async_processing"])` is called. It was **broken by
   the deliberate fix** that replaced autodiscovery with explicit task imports
   (autodiscovery did not actually import the modules, so enqueue failed with
   "task not registered"). **The fix is correct; the test now encodes the old,
   broken behaviour and should be updated to assert the task modules are
   imported.**
2. **`test_initial_migration_declares_every_current_model_table`** requires the
   *initial* migration to declare every current model table. `datasets` and
   `dataset_features` were added in a later migration (`a90513d23268`), so this
   premise is incompatible with incremental migrations. It broke when the dataset
   models landed.

No frontend test runner is configured (no vitest/jest in `frontend/package.json`).

### 6.8 Living Earth / 3D Globe — ⏸️ DEPRIORITIZED

**This work is not on `main`.** It lives entirely on
`archive/living-earth-experiment` (`630809f`), which is also the commit `main`
pointed at before PR #1 superseded it.

Verified by file count on each branch:

| Subsystem | on `main` | on archive |
| --- | --- | --- |
| atmosphere | 0 | 7 |
| clouds | 0 | 10 |
| night lights | 0 | 9 |
| ephemeris | 0 | 3 |
| choreography | 0 | 12 |
| telemetry | 0 | 4 |
| terrain | 2 (config + a `.bak`) | 8 |
| ocean | 1 (`.bak`) | 5 |

Honest classification of that work — **terrain, ocean, atmosphere, clouds, night
lights, stars, sun/moon, telemetry, performance framework, choreography**:

- **Implemented:** yes, as code, on the archive branch
- **Runtime verified:** ❓ not in this session
- **Visually verified:** ❓ **no** — there is no evidence in this session that any
  of it was ever seen working

**Do not claim the Living Earth system is complete.** It was archived precisely
because the direction went too far into planetary rendering. `main` deliberately
carries a stable 2D map instead, and `ec82b99` explicitly disabled dead terrain
tile fetching.

`nightTexture` — ❓ **cannot be assessed.** It appears in 2 files on the archive
branch and **zero** files on `main`. No binding warning was observed or
investigated in this session; any prior report of it is unverified here.

### 6.9 Prettier — ⏸️ not enforced

`prettier` and `prettier-plugin-tailwindcss` are devDependencies; the only script
is `format: prettier --write .` (there is **no** `format:check`). CI does **not**
run it.

**152 files** currently differ from the configured style. This is a
config/codebase mismatch, not simple untidiness: `.prettierrc` sets
`semi: false` while **83 of 156** source files use semicolons. A single 184-line
file produces 340 changed lines. The tailwind plugin also **reorders class
names** (`"w-3 h-3"` → `"h-3 w-3"`).

⚠️ **`pnpm-lock.yaml` is not in `.prettierignore`** — running `prettier --write .`
would reformat the lockfile, along with `package.json`, `pnpm-workspace.yaml`,
`eslint.config.js` and `README.md`. Add exclusions **before** anyone runs it.

---

## 7. Important Root Causes Previously Discovered

### 7.1 Backend could not boot — rasterio coupling

```
WHAT WAS WRONG  api/dependencies.py, imported by every router, eagerly imported
                COGRasterProvider and RasterPolygonizer at module scope.
WHY IT BROKE    Both pull in rasterio. One unloadable binary made the ENTIRE API
                unimportable, including endpoints that never touch raster data.
                rasterio is not architecturally required at startup.
FIX             Both providers now import rasterio inside their provider
                functions and translate ImportError into HTTP 503.
VERIFIED        Backend boots; vector endpoints 200 while rasterio is unloadable;
                raster endpoints 503 with an actionable message.
STATUS          ✅ Fixed and merged.
```

### 7.2 Docker `libexpat1`

```
WHAT WAS WRONG  import rasterio failed in the container:
                "libexpat.so.1: cannot open shared object file"
WHY IT BROKE    The manylinux wheel bundles GDAL, but that bundled GDAL still
                links against the SYSTEM libexpat.so.1, which python:3.13-slim
                omits. An initial assessment that "no system packages are
                needed" was WRONG.
FIX             apt-get install libexpat1. Determined by running ldd over every
                .so in rasterio and rasterio.libs — it was the ONLY unresolved
                dependency. No libgdal-dev needed (saves ~300MB and avoids a
                clash with bundled GDAL 3.12.4).
VERIFIED        rasterio 1.5.1 + GDAL 3.12.4 import in-container.
STATUS          ✅ Fixed and merged.
```

### 7.3 `python-multipart` missing

```
WHAT WAS WRONG  Container crash-looped:
                RuntimeError: Form data requires "python-multipart".
WHY IT BROKE    The upload endpoint uses UploadFile, which needs it. It was in
                the local venv — so uploads always worked in development — but
                never pinned in requirements.txt. Any environment built from
                that file failed at STARTUP, not at request time.
FIX             Pinned python-multipart==0.0.32. pip freeze vs requirements.txt
                showed it was the only drift.
VERIFIED        Container boots; multipart upload returns 201.
STATUS          ✅ Fixed and merged.
```

### 7.4 CORS origin mismatch

```
WHAT WAS WRONG  ALLOWED_ORIGINS listed only port 5173; the frontend moved to 5273.
WHY IT BROKE    Every browser request blocked while curl kept working — the
                classic "API fine, map empty" failure.
FIX             Added the 5273 origins; corrected the config default off
                http://localhost:3000 (a leftover pointing at the deleted
                Next.js scaffold).
VERIFIED        Preflight 200 with access-control-allow-origin: localhost:5273.
STATUS          ✅ Fixed and merged.
```

### 7.5 Environment configuration was misleading

```
WHAT WAS WRONG  1. Root .env.example documented API_CORS_ORIGINS — referenced
                   NOWHERE in the codebase. Settings uses extra="ignore", so
                   setting it was silently discarded.
                2. apps/backend/.env.example did not exist at all.
                3. frontend/.env.example said http://localhost:8000, missing the
                   /api/v1 suffix → 404 on every request from a fresh checkout.
WHY IT BROKE    A developer following the examples got a non-functional setup
                with no error explaining why.
FIX             Canonical variable is ALLOWED_ORIGINS. Created
                apps/backend/.env.example; corrected the frontend URL; removed
                dead keys (API_ENV, REDIS_HOST/PORT, POSTGRES_HOST/PORT).
                Documented that list[str] parses as JSON — a comma-separated
                value raises SettingsError — and that env_file is cwd-relative.
VERIFIED        .env.example loaded through Settings yields a usable config.
STATUS          ✅ Fixed and merged.
```

### 7.6 Raster AOI windowing ignored

```
WHAT WAS WRONG  _resolve_window returned None unconditionally. An
                area_of_interest was accepted, validated, then discarded, and
                the caller received WHOLE-RASTER statistics with HTTP 200 and no
                indication.
WHY IT MATTERS  A natural-language layer would emit an AOI with no human
                checking whether the response reflected it.
FIX             Converts the bbox to a PixelWindow using the raster's affine
                transform (inverse of a north-up affine: col=(x−c)/a,
                row=(y−f)/e), clamps to extent, and RAISES rather than silently
                widening for rotated transforms, zero pixel size, non-lon/lat
                CRS, or a non-intersecting AOI.
VERIFIED        Each third of a 3-region raster returns uniform values at
                exactly 4800/14400 px.
STATUS          ✅ Fixed and merged.
```

### 7.7 Band metadata discarded → wrong-but-plausible results

```
WHAT WAS WRONG  COGRasterProvider populated only identifier/dtype/nodata,
                discarding ds.descriptions. _resolve_bands then mapped bands
                POSITIONALLY, ignoring names.
WHY IT BROKE    NDVI and NDWI are both (band1−band2)/(band1+band2), so requesting
                the wrong index for a raster returned plausible numbers and NO
                error — nothing downstream could detect it.
FIX             Provider surfaces descriptions; band resolution prefers labels
                and raises if a required band is absent. Unlabelled rasters keep
                positional behaviour for compatibility.
VERIFIED        NDVI on a GREEN/NIR raster now returns 400 explaining the
                mismatch, where it previously returned 200 with NDWI's numbers.
                An unlabelled raster still returns mean 0.5 as before.
STATUS          ✅ Fixed and merged.
```

### 7.8 MapLibre discards non-numeric feature ids

```
WHAT WAS WRONG  Backend GeoJSON carries UUID feature ids. MapLibre drops
                non-numeric top-level ids, so queryRenderedFeatures returned
                features with no usable id and click hit-testing silently could
                not work at all.
FIX             The renderer mirrors each UUID into properties.__feature_id.
VERIFIED        Clicking a polygon resolves to the correct feature on a
                1,188-feature dataset.
STATUS          ✅ Fixed and merged. Do not remove this mirroring.
```

### 7.9 Celery task registration

```
WHAT WAS WRONG  autodiscover_tasks(["src.async_processing"]) did not import the
                task modules. FastAPI's enqueue failed with "task not
                registered" while the worker started cleanly and looked healthy
                — the two processes keep separate registries.
FIX             Explicit imports after `app` is created, with
                # noqa: E402, F401 and a comment.
VERIFIED        Worker lists both tasks under [tasks] on startup.
STATUS          ✅ Fixed — BUT it broke test_autodiscovery_enabled (§6.7), and
                `ruff --fix` will delete those imports if the noqa is removed.
```

### 7.10 deck.gl / globe issues — ❓ NOT ASSESSED

Rendering problems from the earlier globe work (including anything relating to
`nightTexture`) are **not** reproducible from `main`, since that code lives only
on the archive branch. **No claim is made here about whether they were solved.**
Treat any earlier report of them as unverified.

---

## 8. Repository Structure

```
TerramindAI/
├── apps/
│   ├── backend/                    FastAPI service
│   │   ├── alembic/                migrations (3 revisions, head a90513d23268)
│   │   ├── scripts/                smoke_test.py, start/stop_services.ps1
│   │   ├── src/
│   │   │   ├── ai/                 SegFormer CV inference (NOT an LLM layer)
│   │   │   ├── analytics/          indices, statistics, COG provider
│   │   │   ├── api/                v1 routers + dependencies
│   │   │   ├── async_processing/   Celery app, tasks, worker
│   │   │   ├── core/               config, exceptions, logging, redis
│   │   │   ├── db/                 session + SQLAlchemy models
│   │   │   ├── geospatial/         polygonizer, geometry, GeoJSON export
│   │   │   ├── repositories/       data access incl. dataset_repository
│   │   │   ├── schemas/            Pydantic API schemas
│   │   │   ├── services/           dataset/analysis/project services
│   │   │   └── main.py             app = create_app()
│   │   ├── tests/                  43 test files (2 failing, not in CI)
│   │   ├── .env.example
│   │   ├── pyproject.toml          ruff + mypy config
│   │   └── requirements*.txt
│   └── frontend/                   ⚠️ DEAD Next.js scaffold — ignore entirely
├── frontend/                       THE REAL FRONTEND (Vite + React + MapLibre)
│   └── src/{core,features,components,stores,...}
├── docker/
│   └── Dockerfile.backend
├── scripts/
│   ├── start_stack.ps1
│   └── stop_stack.ps1
├── datasets/
│   └── bangalore_osm.geojson       1,188 real OSM features
├── docs/                           empty (.gitkeep)
├── packages/  infrastructure/      empty (.gitkeep)
├── docker-compose.yml
├── .dockerignore
├── .env.example                    docker-compose only
├── README.md
├── ROADMAP.md
├── walkthrough.md                  detailed verification log
└── CURRENT_STATE.md                this file
```

⚠️ `apps/frontend/` is a dead Next.js scaffold. Do not build anything there.
⚠️ `ruff.zip` (11 MB) and `ruff-bin/` are committed at the repo root.

---

## 9. Important Files

### Backend

```
src/main.py                                  app factory, CORS, middleware
src/core/config.py                           Settings — ALLOWED_ORIGINS lives here
src/api/dependencies.py                      DI wiring; lazy rasterio imports
src/api/v1/router.py                         router aggregation
src/api/v1/{datasets,analysis,ai,geospatial,projects,health,jobs}.py
src/services/dataset_service.py              upload, metadata, spatial queries
src/services/analysis_service.py             raster pipeline; AOI + band resolution
src/repositories/dataset_repository.py       raw PostGIS SQL (ST_DWithin etc.)
src/analytics/providers/cog_provider.py      rasterio reader; band descriptions
src/analytics/indices/{ndvi,ndwi,registry}.py
src/analytics/statistics/engine.py
src/geospatial/polygonizer.py                raster → vector (rasterio.features)
src/geospatial/interfaces.py                 PolygonizerProtocol
src/db/models/{dataset,dataset_feature,project,base}.py
src/async_processing/celery_app.py           ⚠️ explicit task imports + noqa
apps/backend/tests/                          43 files
```

### Frontend

```
src/features/earth/services/EarthEngine.ts               map lifecycle singleton
src/features/earth/services/MapLibreDatasetRenderer.ts   THE live render path
src/features/earth/services/style-expression-compiler.ts DatasetStyle → MapLibre
src/features/earth/services/categorical-style.ts         palette + categories
src/features/earth/stores/use{Nearby,Contains,Intersects}QueryStore.ts
src/features/earth/stores/useDatasetStyleStore.ts
src/features/datasets/components/{Dataset,Nearby,Contains,Intersects,Style}*.tsx
src/features/datasets/hooks/useDatasetManager.ts
src/core/datasets/                                       registry, importers
src/core/styles/{style.types,style-evaluator}.ts         deck.gl-path evaluator
src/stores/useProjectStore.ts
src/main.tsx                     exposes window.EarthEngine for debugging
```

### AI (computer vision — **not** LLM)

```
src/ai/base.py            AbstractAIModel
src/ai/registry.py        ModelRegistry
src/ai/manager.py         ModelManager
src/ai/service.py         AIInferenceService
src/ai/models.py          InferenceRequest / InferenceResult
src/ai/providers/segformer.py
src/ai/processing/{preprocessor,postprocessor}.py
src/api/v1/ai.py          POST /api/v1/ai/inference
```

### Docker

```
docker/Dockerfile.backend      python:3.13-slim + libexpat1 + curl
docker-compose.yml             db, redis, backend, celery_worker
.dockerignore                  excludes .env, .venv, node_modules
apps/backend/requirements.txt  84 pins + PyTorch CPU --extra-index-url
apps/backend/requirements-dev.txt / requirements-ai.txt
```

### Documentation

```
walkthrough.md      detailed verification log (§1–18)
CURRENT_STATE.md    this handoff
README.md           setup + spatial query summary
ROADMAP.md          ⚠️ stale — only documents Milestone 11.1 repo setup
```

---

## 10. Commands

All verified from `package.json`, `pyproject.toml`, the scripts and CI.

### Full stack (Windows / PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_stack.ps1
powershell -ExecutionPolicy Bypass -File scripts\stop_stack.ps1
powershell -ExecutionPolicy Bypass -File scripts\stop_stack.ps1 -Containers
```

Runs containers → migrations → Celery → FastAPI → Vite, verifying each layer.
Native backend on `:8000`, frontend on `:5273`.

### Docker

```bash
docker compose up -d db redis            # dependencies only
docker compose up -d                     # + backend and celery_worker
docker compose build backend             # rebuild image
docker compose ps
docker compose logs backend --tail 50
docker compose logs celery_worker --tail 50
docker compose down
```

⚠️ The containerised backend and `start_stack.ps1` both bind `:8000`. Run one or
the other, or set `BACKEND_PORT`.

### Backend (native)

```powershell
cd apps\backend
$env:PYTHONPATH = (Get-Item .).FullName     # required
.venv\Scripts\python.exe -m uvicorn src.main:app --port 8000
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m alembic current
.venv\Scripts\python.exe -m celery -A src.async_processing.celery_app worker -l info --pool=solo
```

⚠️ Must run from `apps/backend` — `env_file` is cwd-relative.
⚠️ `--pool=solo` is required on Windows (billiard permission errors). Not needed
in Docker.

### Backend quality gates

```bash
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy src/
.venv/Scripts/python.exe -m pytest            # NOT run by CI; 2 failures
```

⚠️ Never run `ruff --fix` blindly on `celery_app.py` — it deletes the task
registration imports.

### Frontend

```bash
cd frontend
pnpm dev --port 5273 --strictPort
pnpm lint
pnpm type-check
pnpm build
pnpm format                 # ⚠️ rewrites 152 files incl. pnpm-lock.yaml
```

Package manager is **pnpm**, not npm.

### Health / endpoint verification

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/ready
curl http://127.0.0.1:8000/api/v1/projects
curl "http://127.0.0.1:8000/api/v1/projects/{pid}/datasets"
curl "http://127.0.0.1:8000/api/v1/projects/{pid}/datasets/{did}/geojson"
curl "http://127.0.0.1:8000/api/v1/projects/{pid}/datasets/{did}/query/nearby?lon=77.55&lat=12.95&radius_meters=2000"
docker exec terramindai-db-1 psql -U terramind -d terramind_db -c "\dt"
```

API docs: `http://127.0.0.1:8000/docs`

---

## 11. Current Runtime State

Verified at generation time, not assumed.

```
CURRENT RUNTIME: RUNNING
```

| Component | State | Detail |
| --- | --- | --- |
| Frontend (Vite) | ✅ RUNNING | host process, `http://localhost:5273` → 200 |
| Backend (FastAPI) | ✅ RUNNING | **in Docker**, `:8000` → `/health` 200, `/ready` 200 |
| PostgreSQL/PostGIS | ✅ RUNNING | container `terramindai-db-1`, healthy, `:5432` |
| Redis | ✅ RUNNING | container `terramindai-redis-1`, healthy, `:6379` |
| Celery worker | ✅ RUNNING | container `terramindai-celery_worker-1`, healthy |
| Docker | ✅ RUNNING | all four services healthy |
| Native backend | ⏹️ STOPPED | deliberately — the container owns `:8000` |

Environment assumptions: Docker Desktop running; `apps/backend/.env` and
`frontend/.env` present locally (both gitignored); venv at `apps/backend/.venv`
(Python 3.13.14).

Database contents:

```
bangalore osm   1188 features   Mixed
test data          3 features   Mixed   (×3 duplicates)
```

---

## 12. Git State

```
Branch          : main
HEAD            : 3f5c92e  Merge pull request #4 from ronitsaha11/feat/backend-docker
origin/main     : 3f5c92e  (in sync)
Uncommitted     : CURRENT_STATE.md (this file, untracked) — nothing else
Pushed          : yes, all work through PR #4 is merged and pushed
```

Remote branches:

```
main                             3f5c92e6   current
feat/backend-docker              9558c011   merged via PR #4
fix/config-reproducibility       7c9b2386   merged via PR #3
feat/attribute-styling           efe893f2   merged via PR #2
main-map-baseline                26b50c96   merged via PR #1
archive/living-earth-experiment  630809f7   archived 3D globe work
```

**SAFE BASELINE: `3f5c92e` on `main`.** All four PRs merged with CI green on
`main` after each.

**No commit was created and nothing was pushed while generating this document.**

---

## 13. Phase History

| Stage | What happened |
| --- | --- |
| **Initial frontend/map** | Vite + React + MapLibre workspace; panels, stores, layer architecture |
| **Living Earth experiment** | 15 commits: simulation clock, ephemeris, camera framework, streaming, terrain, atmosphere, clouds, night lights, space environment, choreography, performance framework, telemetry |
| **Course correction** | Direction judged too far into planetary rendering; branch `main-map-baseline` stepped back to a stable 2D map. `ec82b99` disabled dead terrain tiles. |
| **Dataset infrastructure** | PostGIS `datasets`/`dataset_features`, GeoJSON import, registry, metadata computed from real files |
| **Spatial engine** | `ST_DWithin` (geography cast), `ST_Contains`, `ST_Intersects`; click-to-query UI |
| **Styling (Phase 4)** | `DatasetStyle` compiled to MapLibre expressions; Okabe-Ito palette; legend |
| **PR #1** | Superseded `main` (which still held the Living Earth work) via a `-s ours` merge; the experiment preserved on `archive/living-earth-experiment` |
| **CI repair** | CI had been linting the dead `apps/frontend` scaffold; repointed to the real frontend. Backend install was impossible (`torch==2.13.0+cpu` not on PyPI). |
| **Config hardening** | Canonical `ALLOWED_ORIGINS`; created the missing backend `.env.example`; fixed a frontend example URL that 404'd |
| **Docker hardening** | Backend containerised; `libexpat1` and `python-multipart` bugs found and fixed |
| **Analytics correctness** | AOI windowing implemented; band-label validation added |
| **Now** | Core Earth Intelligence objective; Phase 5 next |

**Living Earth — implementation vs verification**

```
Implemented       ✅  code exists on archive/living-earth-experiment
Runtime verified  ❓  not in this session
Visually verified ❓  NO evidence it was ever seen working
```

---

## 14. Current Product Direction

Focus is the **core TerraMind objective: natural-language Earth Intelligence
over real geographic datasets.** Not decorative 3D globe features.

```
User
 ↓ natural-language geographic question
Claude API
 ↓ constrained structured query
Backend validation
 ↓
Existing spatial engine        ← already built and verified
 ↓
Dataset Registry               ← already built and verified
 ↓
PostGIS / raster analytics     ← already built and verified
 ↓
GeoJSON                        ← contract already used by the map
 ↓
Existing map                   ← already renders and styles this
 ↓
Useful geographic answer
```

**The existing spatial engine is the trusted geographic computation layer.** The
model interprets intent; TerraMind computes geography.

---

## 15. Important Architectural Decisions

Preserve these.

**LLM provider**

- Claude API is the LLM provider for the AI layer
- Credentials stay **server-side only**
- The frontend must **never** contain the Claude API key

**Hard boundaries on what Claude may do**

- ❌ Must not generate raw SQL
- ❌ Must not execute SQL
- ❌ Must not access PostGIS directly
- ❌ Must not generate arbitrary Python/GIS code
- ❌ Must not bypass backend validation
- ✅ Responsible for interpreting user intent — nothing more

**Reuse, do not rebuild**

- Reuse the existing spatial primitives (`nearby`, `contains`, `intersects`)
- Reuse the existing Dataset Registry
- Preserve the existing GeoJSON contracts — the map already renders them
- Reuse the existing map infrastructure
- Avoid broad architectural rewrites

**Working practice**

- Diagnose before modifying
- Verify actual behaviour; do not trust logs, 200s or successful builds
- "I changed it" and "I verified it works" are different claims

**Project-specific constraints**

- `MapLibreDatasetRenderer` is the live render path, **not** deck.gl
- Keep `properties.__feature_id` mirroring — click hit-testing depends on it
- Keep the explicit Celery task imports and their `noqa`
- `ST_DWithin` needs `::geography` on **both** sides
- Timestamps must stay `DateTime(timezone=True)`
- `pnpm`, not npm; backend starts from `apps/backend`

---

## 16. Phase 5 Boundary

Phase 5 is **Natural Language Spatial Intelligence using the Claude API**.

```
Natural Language → Claude → Structured Query → Validation
  → Existing Spatial Primitive → Dataset Registry → GeoJSON → Existing Map
```

**The detailed Phase 5 implementation prompt is deliberately not in this file.**

The next session should:

1. Read this document
2. Inspect the actual repository
3. Verify the handoff against reality
4. **Then** receive the separate Phase 5 implementation prompt

**Nothing in Phase 5 has been started.** No LLM code, no prompt engineering, no
NL parser, no chat UI, no API-key handling exists.

A suggested seam — not a specification — recorded for context: a backend
endpoint (e.g. `POST /api/v1/projects/{id}/query/natural`) that maps intent onto
an existing spatial primitive and returns the **same `FeatureCollection` shape
the map already renders**, so no rendering work is needed. Having the model emit
a constrained, validated structure rather than SQL keeps it testable without a
live model and avoids injection risk.

⚠️ **Unresolved decision:** where the Claude API key lives (env var, secret
manager) has not been decided.

---

## 17. What Must NOT Be Assumed

The next session must **not** assume:

- ❌ that every previous "completion report" was accurate
- ❌ that every implemented component is visually working
- ❌ that the Living Earth system is production-ready — **it is on an archive
  branch and was never visually verified**
- ❌ that deck.gl features work
- ❌ that atmosphere / cloud / star / night-light features work
- ❌ that telemetry is functional
- ❌ that unverified features are complete
- ❌ that a successful build means runtime success
- ❌ that a 200 response means the geographic result is **correct** — §7.6 and
  §7.7 are both cases where 200 was returned with the wrong answer
- ❌ that `src/ai/` is LLM scaffolding — **it is computer vision**
- ❌ that the test suite is green — **2 tests fail and CI does not run it**

**The repository and direct runtime evidence are the source of truth.**

---

## 18. Final Handoff Summary

### Current project status

TerraMind has a genuinely working vector Earth Intelligence pipeline: a real
PostGIS dataset registry, three verified spatial query primitives, and a 2D
MapLibre map that renders and styles 1,188 real OSM features with correct
geometry, correct CRS, and working pan/zoom. Raster analytics (NDVI, NDWI,
statistics, AOI windowing) are verified correct against hand-calculated values —
**but only inside Docker**, because Windows Smart App Control blocks rasterio on
the host. The backend runs both natively (raster degrades to a clear 503) and
containerised (raster works). Four PRs are merged with CI green. What does
**not** exist is any natural-language layer: there is no LLM code in the
repository at all, and the `src/ai/` package is computer-vision inference for
raster segmentation, not an LLM integration. The most significant unaddressed
risks are a test suite that CI never runs (with 2 real failures), and a large
body of archived 3D globe work that was implemented but never verified working.

### ✅ VERIFIED

Backend boot · health · readiness · PostgreSQL/PostGIS · Redis · Celery task
registration · CORS · projects API · dataset upload/list/retrieve · `ST_DWithin`
/ `ST_Contains` / `ST_Intersects` (all cross-checked against raw SQL) · 2D map
rendering of 1,188 features with 0 invalid geometries · attribute styling
including the grey fallback · pan · zoom · viewport-dependent feature counts ·
NDVI · NDWI · raster statistics · AOI windowing · band-label validation ·
positional fallback · raster error handling · Docker containerisation · all six
lint/type/build gates

### ⚠️ PARTIALLY VERIFIED

- **Map visual confirmation** — came from user-supplied screenshots, not agent
  capture; the automated browser pane never composited
- **Test suite** — ~146 pass, **2 fail**, and CI does not run it
- **RasterPolygonizer** — instantiates, never exercised end-to-end
- **Celery** — tasks registered, but no job executed through the queue

### ❓ UNVERIFIED

- SegFormer AI inference end-to-end (and it is not wired to the frontend)
- Everything on `archive/living-earth-experiment`
- `nightTexture` behaviour — exists only on the archive branch; no evidence here

### ❌ BROKEN

- rasterio on the native Windows host (environment — Smart App Control)
- `test_autodiscovery_enabled` (encodes behaviour that was deliberately fixed)
- `test_initial_migration_declares_every_current_model_table` (premise
  incompatible with incremental migrations)
- No dataset DELETE endpoint

### ⏸️ DEPRIORITIZED

Living Earth / 3D globe in full — terrain, ocean, atmosphere, clouds, night
lights, stars, sun/moon, telemetry, performance framework, choreography ·
Prettier formatting gate · containerising the frontend

### Current strategic objective

```
Build TerraMind's Natural Language Spatial Intelligence layer.
```

### LLM provider

```
Claude API
```

### Next session

1. This `CURRENT_STATE.md` is the persistent handoff
2. Start a fresh Claude Code conversation
3. It receives the full repository
4. It reads and **verifies** this document against reality
5. The Phase 5 implementation prompt is then provided separately
6. Phase 5 begins only after the repository state is confirmed

### Primary next action

**Start a fresh Claude Code session and have it verify this handoff against the
actual repository before making any Phase 5 changes.**

### Safe baseline

```
main @ 3f5c92e — "Merge pull request #4 from ronitsaha11/feat/backend-docker"
All four PRs merged, CI green on main after each.
```

### Blockers

**Genuine blockers for Phase 5:**

1. **The Claude API key decision** — provider account and where the key lives.
   This is a product decision, not a technical one, and no code should be written
   until it is made.

**Not blockers** (they can proceed in parallel): native rasterio, the two failing
tests, Prettier, the missing DELETE endpoint, the archived globe work. Phase 5
targets the vector pipeline, which is verified working.
