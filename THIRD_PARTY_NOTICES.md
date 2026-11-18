# Third-party components

TerraMind AI uses the third-party software, models, data and services listed
here. Each remains under its own terms, which this repository does not change.
For TerraMind's own code, see [Licence](README.md#licence) in the README: no
licence has been granted.

Recorded on 18 November 2026 from upstream licence files, model cards and
provider terms. Terms change; check the linked source before relying on an
entry. This is an inventory, not legal advice.

## External services called at runtime

| Service | Called by | When | Terms and attribution |
| --- | --- | --- | --- |
| CARTO basemap (Dark Matter style, vector tiles, glyphs and sprite from `basemaps.cartocdn.com` and `tiles.basemaps.cartocdn.com`) | Frontend | Every map load | [Basemap Terms](https://carto.com/legal/basemap-terms/). Attribution "© OpenStreetMap contributors, © CARTO" must stay visible on the map. The terms tie free use to a CARTO-issued API key passed as a `key` parameter and set monthly request limits; the frontend currently requests the basemap without a key. |
| Google Gemini API | Backend (`/query/natural`) | Each natural-language question | [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms). On unpaid quota, Google may use submitted content to improve its products, and human reviewers may read inputs and outputs. The terms require Paid Services when the app is offered to users in the EEA, Switzerland or the UK. |
| Element 84 Earth Search (`EARTH_SEARCH_URL`) | Backend scene search | Only when the scene search API is called | Public STAC catalogue. The Sentinel-2 data it indexes is Copernicus Sentinel data, offered with "free, full and open" access under the Copernicus Sentinel data terms; check those terms for the attribution wording before publishing derived products. |
| TiTiler at `titiler.xyz` (`TITILER_URL`) | Backend scene tiles | Only when a scene tile template is requested | A publicly hosted third-party instance. No service terms were found; deploy your own TiTiler for production. |

Configured but not called: the MapLibre demo terrain tiles
(`frontend/src/features/earth/config/terrain.config.ts`). Terrain is disabled
in code, so the URL is never requested. The service exists for MapLibre's own
examples and tests.

## Machine-learning models

| Model | How it is obtained | Terms |
| --- | --- | --- |
| [`nvidia/segformer-b0-finetuned-ade-512-512`](https://huggingface.co/nvidia/segformer-b0-finetuned-ade-512-512) | Downloaded from Hugging Face at runtime by `transformers`; not stored in this repository. No revision is pinned; the current model revision is `489d5cd8`. | Model card licence: "other", pointing to the [NVIDIA Source Code License for SegFormer](https://github.com/NVlabs/SegFormer/blob/master/LICENSE), which permits use for non-commercial (research or evaluation) purposes only. The weights are fine-tuned on ADE20K, whose images MIT CSAIL makes available for non-commercial research and educational use. |

## Data in this repository

| File | Terms |
| --- | --- |
| [`datasets/bangalore_osm.geojson`](datasets/README.md) | © OpenStreetMap contributors, [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Provenance and changes are recorded in [`datasets/README.md`](datasets/README.md). |
| `docs/images/nlq-hospitals-near-lalbagh.jpg` | Screenshot of TerraMind. The map in it shows CARTO basemap and OpenStreetMap data, credited in its caption in the README. |

## Software dependencies

Installed from PyPI and npm, not vendored. Each package is under its own
licence; see the package metadata for the full text.

**Python** (`apps/backend/requirements.txt`, `requirements-dev.txt`):
predominantly MIT, BSD and Apache-2.0. `certifi`, `pathspec` and `tqdm` include
MPL-2.0 terms. Several wheels bundle native libraries, each with its own
licence (listed from the Windows wheels; Linux wheels differ in detail):

| Package | Bundled native libraries (examples) | Notes |
| --- | --- | --- |
| `rasterio` 1.5.1 (BSD-3-Clause) | GDAL, GEOS, PROJ, HDF5, libtiff, libjpeg, libcurl | GEOS is LGPL-2.1. |
| `shapely` 2.1.2 (BSD-3-Clause) | GEOS | GEOS is LGPL-2.1; its licence ships in the wheel. |
| `pyproj` 3.7.2 (MIT) | PROJ, libcurl, SQLite, libtiff | |
| `torch` 2.13.0+cpu (Apache-2.0 and others) | Many | Third-party licences ship in the wheel under `third_party/`. |

These obligations matter if TerraMind is distributed (for example as a
container image or installer), not only when it runs as a hosted service.

**JavaScript** (`frontend/package.json`): production packages are MIT, ISC,
BSD and Apache-2.0, plus `jszip` (offered as MIT or GPL-3.0-or-later) and
`lightningcss` (MPL-2.0, build tooling). Development tooling additionally
includes `caniuse-lite` (CC-BY-4.0, browser-support data used at build time).
Key versions: `maplibre-gl` 6.0.0 (BSD-3-Clause), `react` 19.2.8 (MIT),
`lucide-react` 1.27.0 (ISC, used for interface icons).

## Fonts, icons and images

- **Map fonts** (Montserrat, Open Sans, Noto Sans) are served by CARTO as map
  glyphs; none are bundled in this repository.
- **Interface icons** come from `lucide-react` (ISC).
- **`frontend/public/favicon.svg` and `frontend/public/icons.svg`** come from
  the Vite starter template. `icons.svg` contains other organisations' brand
  marks (Bluesky, Discord, GitHub) and is not referenced by the app.
