import type { CameraState, CameraUpdateOptions } from './CameraTypes';
import { CameraMath } from './CameraMath';
import { type CameraConfig, DEFAULT_CAMERA_CONFIG } from './CameraConfig';

export class CameraValidation {
  /**
   * Validates and sanitizes a partial camera update into a full valid camera state.
   * Modifies the `outState` object in place to avoid allocations.
   */
  public static applyUpdate(
    currentState: Readonly<CameraState>,
    update: CameraUpdateOptions,
    outState: CameraState,
    config: CameraConfig = DEFAULT_CAMERA_CONFIG
  ): void {
    // Latitude [-90, 90]
    const lat = CameraMath.safeNumber(update.latitude, currentState.latitude);
    outState.latitude = CameraMath.clamp(lat, -90, 90);

    // Longitude [-180, 180] wrapping
    const lon = CameraMath.safeNumber(update.longitude, currentState.longitude);
    // Normalize to [-180, 180]
    let normLon = lon % 360;
    if (normLon > 180) normLon -= 360;
    else if (normLon < -180) normLon += 360;
    outState.longitude = normLon;

    // Altitude clamped to configured limits
    const alt = CameraMath.safeNumber(update.altitude, currentState.altitude);
    outState.altitude = CameraMath.clamp(alt, config.minAltitude, config.maxAltitude);

    // Pitch clamped to configured limits
    const pitch = CameraMath.safeNumber(update.pitch, currentState.pitch);
    outState.pitch = CameraMath.clamp(pitch, config.minPitch, config.maxPitch);

    // Bearing wrapped to [0, 360)
    const bearing = CameraMath.safeNumber(update.bearing, currentState.bearing);
    outState.bearing = CameraMath.normalizeBearing(bearing);
  }
}
