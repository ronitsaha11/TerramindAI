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
