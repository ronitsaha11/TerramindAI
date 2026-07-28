import type { Vector3, EarthState } from '../../../core/planet';

/**
 * Lightweight rendering approximation for global illumination.
 * Translates the true Earth Ephemeris state into a rendering-friendly Sun direction.
 */
export class SunLightingMath {
  /**
   * Updates a pre-allocated Vector3 in place with the computed Sun direction.
   * Based on the Earth's rotation angle from J2000.
   * This is a deterministic visualization approximation.
   *
   * @param earthState The canonical Earth state
   * @param outVector The vector to mutate in place
   * @returns the mutated outVector for convenience
   */
  public static calculateSunDirectionEcef(earthState: Readonly<EarthState>, outVector: Vector3): Vector3 {
    // Basic approximation: 
    // The sun is roughly on the equatorial plane for a simplified global illumination model,
    // or we can add seasonal tilt later if needed. For now, it rotates counter to the Earth's rotation.
    
    // Convert ERA (Earth Rotation Angle) to radians
    const eraRad = (earthState.rotationAngleDegrees * Math.PI) / 180.0;
    
    // For a sun positioned at "noon" relative to the prime meridian when ERA = 0,
    // the sun is at X=1, Y=0. As Earth rotates positively (East), the Sun appears to move West (negative angle).
    const sunAngle = -eraRad;
    
    // Note: Assuming a 23.44 degree axial tilt for a more realistic lighting model could be added here
    // by rotating the vector around the Y axis, but a simple equatorial orbit serves Phase B4's requirements.

    outVector.x = Math.cos(sunAngle);
    outVector.y = Math.sin(sunAngle);
    outVector.z = 0; // Equatorial approximation
    
    return outVector;
  }
}
