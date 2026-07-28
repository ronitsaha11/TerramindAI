import type { CelestialVector, StarConfig } from './SpaceTypes';

export interface SpaceState {
  sunDirectionEci: CelestialVector;
  moonPositionEci: CelestialVector;
  moonPhase: number;
  celestialRotationDegrees: number;
  starConfig: StarConfig;
  backgroundColor: [number, number, number];
}
