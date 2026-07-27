# TerraMind AI Frontend

This is the frontend application for the TerraMind Earth Intelligence Platform.

## Technology Stack
- React
- TypeScript
- Vite
- pnpm

## Directory Overview
- `src/app/`: Application core config.
- `src/assets/`: Static assets.
- `src/components/`: Reusable UI and feature components.
- `src/features/`: Feature modules.
- `src/hooks/`: Custom hooks.
- `src/layouts/`: Page layouts.
- `src/lib/`: Third-party configurations.
- `src/routes/`: Route definitions.
- `src/services/`: API and services.
- `src/stores/`: State management.
- `src/styles/`: Global styles.
- `src/types/`: TypeScript definitions.
- `src/utils/`: Utilities.
- `tests/`: Tests.

## Setup Instructions

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Set up environment variables:
   Copy `.env.example` to `.env` and configure accordingly.
   ```bash
   cp .env.example .env
   ```

## Development Commands

- `pnpm run dev`: Start the development server.
- `pnpm run build`: Build the application for production.
- `pnpm exec tsc --noEmit`: Run type checking.
