# TerraMind AI

Earth Intelligence Platform.

## Architecture
- **Frontend**: Next.js
- **Backend API**: FastAPI
- **Database**: PostgreSQL (PostGIS)
- **Cache/Queue**: Redis
- **ML Engine**: PyTorch

## Local Development

### Prerequisites
- Node.js (v18+)
- Python (3.11+)
- Docker & Docker Compose
Added new features
### Getting Started
1. Clone the repository
2. Copy `.env.example` to `.env`
3. Run `docker-compose up -d` to start the database and redis
4. Follow the specific instructions in `apps/frontend` and `apps/backend` to run the services locally.
