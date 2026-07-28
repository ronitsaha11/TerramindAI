import type { LatLon } from './PlanetTypes';

export class PlanetValidation {
  /**
   * Validates that latitude is within [-90, 90] and longitude is within [-180, 180].
   * @throws Error if coordinates are invalid.
   */
  public static assertValidLatLon(latLon: LatLon): void {
    if (latLon.latitude < -90 || latLon.latitude > 90) {
      throw new Error(`[PlanetValidation] Invalid latitude: ${latLon.latitude}. Must be between -90 and 90.`);
    }
    if (latLon.longitude < -180 || latLon.longitude > 180) {
      throw new Error(`[PlanetValidation] Invalid longitude: ${latLon.longitude}. Must be between -180 and 180.`);
    }
  }

  /**
   * Normalizes longitude to the range [-180, 180].
   */
  public static normalizeLongitude(longitude: number): number {
    let normalized = longitude % 360;
    if (normalized > 180) normalized -= 360;
    else if (normalized < -180) normalized += 360;
    return normalized;
  }

  /**
   * Clamps latitude to the range [-90, 90].
   */
  public static clampLatitude(latitude: number): number {
    return Math.max(-90, Math.min(90, latitude));
  }
}
