export class CameraInterpolator {
  /**
   * Linearly interpolates two values.
   */
  public static lerp(start: number, end: number, t: number): number {
    return start + (end - start) * t;
  }

  /**
   * Interpolates longitude, taking the shortest path across the antimeridian if necessary.
   */
  public static lerpLongitude(start: number, end: number, t: number): number {
    let diff = end - start;
    
    // Normalize to [-180, 180]
    while (diff < -180) diff += 360;
    while (diff > 180) diff -= 360;
    
    let current = start + diff * t;
    
    // Normalize the result back to [-180, 180]
    while (current < -180) current += 360;
    while (current > 180) current -= 360;
    
    return current;
  }
}
