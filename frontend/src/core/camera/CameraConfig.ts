import type { CameraState } from './CameraTypes';

export interface CameraConfig {
  /** Maximum allowed pitch in degrees */
  maxPitch: number;
  /** Minimum allowed pitch in degrees */
  minPitch: number;
  /** Maximum altitude in meters */
  maxAltitude: number;
  /** Minimum altitude in meters */
  minAltitude: number;
  /** Default starting camera state */
  initialState: Readonly<CameraState>;
}

export const DEFAULT_CAMERA_CONFIG: CameraConfig = {
  maxPitch: 85,
  minPitch: 0,
  maxAltitude: 20000000, // 20,000 km (deep space view)
  minAltitude: 10,       // 10 meters (street level view)
  initialState: {
    latitude: 20,
    longitude: 0,
    altitude: 10000000,
    pitch: 0,
    bearing: 0,
  },
};
