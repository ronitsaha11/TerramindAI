export class CameraMath {
  /**
   * Normalizes an angle in degrees to [0, 360).
   */
  public static normalizeBearing(degrees: number): number {
    const normalized = degrees % 360;
    return normalized < 0 ? normalized + 360 : normalized;
  }

  /**
   * Clamps a value between a minimum and maximum.
   */
  public static clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value));
  }

  /**
   * Safely returns the number if valid, otherwise returns the fallback.
   * Rejects NaN and Infinity.
   */
  public static safeNumber(value: number | undefined, fallback: number): number {
    if (value === undefined || value === null || isNaN(value) || !isFinite(value)) {
      return fallback;
    }
    return value;
  }
}
