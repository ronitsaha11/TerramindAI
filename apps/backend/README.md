# TerraMind API

## Database setup

Run `alembic upgrade head` from this directory after configuring `DATABASE_URL`.
The initial migration creates every current SQLAlchemy model, enables the required
PostGIS and pgcrypto extensions, and seeds a local development owner.

## Temporary development owner

Authentication is intentionally outside this milestone. Until it is added, project
creation resolves the seeded `development@terramind.local` user rather than assuming
an arbitrary foreign-key UUID exists. The account is created only by the initial
migration and is a local-development bootstrap, not an authentication mechanism.

## Geospatial providers

Milestone 6 uses `httpx` rather than a STAC SDK. The provider boundary owns the
small Earth Search STAC request/normalization surface, keeps external JSON out of
application services, and allows provider adapters to be replaced without changing
routes or services. TiTiler is isolated behind the same pattern for tile metadata
and XYZ templates. Catalog asset references remain provider-normalized URI strings;
the tile service separately accepts HTTP(S) and S3 transport URIs supported by the
configured tile provider. Shared provider HTTP clients are configured at application
lifespan and closed during shutdown.
