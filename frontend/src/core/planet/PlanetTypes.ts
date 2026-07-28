/**
 * Geographic coordinates on the WGS84 ellipsoid.
 */
export interface LatLon {
  /** Latitude in degrees [-90, 90] */
  latitude: number;
  /** Longitude in degrees [-180, 180] */
  longitude: number;
}

/**
 * Geographic coordinates with an altitude.
 */
export interface LatLonAlt extends LatLon {
  /** Altitude in meters above the WGS84 ellipsoid */
  altitude: number;
}

/**
 * 3D Earth-centered Earth-fixed (ECEF) cartesian coordinates.
 * Units are meters.
 */
export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

/**
 * The strongly typed state of the Earth's rotation relative to the J2000 epoch.
 */
export interface EarthState {
  /** 
   * The number of continuous days since the J2000 epoch 
   * (January 1.5, 2000, TT).
   */
  daysSinceJ2000: number;
  
  /** 
   * The Earth Rotation Angle in degrees [0, 360).
   * Represents the rotational state of the Earth.
   */
  rotationAngleDegrees: number;
}
