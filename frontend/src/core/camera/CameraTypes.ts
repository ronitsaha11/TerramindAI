/**
 * Strongly typed representation of the authoritative camera state.
 */
export interface CameraState {
  /** Latitude in degrees [-90, 90] */
  latitude: number;
  /** Longitude in degrees [-180, 180] */
  longitude: number;
  /** Altitude in meters above the reference ellipsoid */
  altitude: number;
  /** Pitch angle in degrees (0 is straight down, up to max configured pitch) */
  pitch: number;
  /** Bearing (heading) in degrees [0, 360), where 0 is true North */
  bearing: number;
}

/**
 * Partial state used for jumping or updating the camera.
 */
export type CameraUpdateOptions = Partial<CameraState>;
