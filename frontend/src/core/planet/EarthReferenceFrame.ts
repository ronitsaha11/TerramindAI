import type { LatLon, LatLonAlt, Vector3 } from './PlanetTypes';
import { EARTH_RADIUS_METERS } from './EphemerisConstants';
import { PlanetValidation } from './PlanetValidation';

/**
 * EarthReferenceFrame is the canonical mathematical reference system for the planet.
 * It is completely independent of time and rotational state.
 * It provides the fundamental spatial boundaries and transformations.
 */
export class EarthReferenceFrame {
  /**
   * Converts Geographic (Lat/Lon/Alt) to Earth-Centered, Earth-Fixed (ECEF) coordinates.
   * Assumes a spherical Earth approximation for deterministic visualization performance,
   * bounded by EARTH_RADIUS_METERS.
   */
  public toECEF(coord: LatLonAlt): Vector3 {
    PlanetValidation.assertValidLatLon(coord);

    const latRad = (coord.latitude * Math.PI) / 180;
    const lonRad = (coord.longitude * Math.PI) / 180;

    const r = EARTH_RADIUS_METERS + coord.altitude;

    // standard spherical to cartesian
    const cosLat = Math.cos(latRad);
    const x = r * cosLat * Math.cos(lonRad);
    const y = r * cosLat * Math.sin(lonRad);
    const z = r * Math.sin(latRad);

    return { x, y, z };
  }

  /**
   * Converts ECEF coordinates back to Geographic (Lat/Lon/Alt).
   */
  public fromECEF(vector: Vector3): LatLonAlt {
    const p = Math.sqrt(vector.x * vector.x + vector.y * vector.y);
    const r = Math.sqrt(p * p + vector.z * vector.z);
    
    if (r === 0) {
      return { latitude: 0, longitude: 0, altitude: -EARTH_RADIUS_METERS };
    }

    const latRad = Math.asin(vector.z / r);
    const lonRad = Math.atan2(vector.y, vector.x);

    const altitude = r - EARTH_RADIUS_METERS;
    const latitude = (latRad * 180) / Math.PI;
    const longitude = (lonRad * 180) / Math.PI;

    return { latitude, longitude, altitude };
  }

  /**
   * Calculates the great-circle distance between two points on the sphere.
   * Uses the Haversine formula.
   */
  public getDistanceMeters(p1: LatLon, p2: LatLon): number {
    PlanetValidation.assertValidLatLon(p1);
    PlanetValidation.assertValidLatLon(p2);

    const lat1 = (p1.latitude * Math.PI) / 180;
    const lat2 = (p2.latitude * Math.PI) / 180;
    const dLat = ((p2.latitude - p1.latitude) * Math.PI) / 180;
    const dLon = ((p2.longitude - p1.longitude) * Math.PI) / 180;

    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return EARTH_RADIUS_METERS * c;
  }
}
