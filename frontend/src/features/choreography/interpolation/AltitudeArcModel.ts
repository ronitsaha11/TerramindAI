import { CameraInterpolator } from './CameraInterpolator';

export class AltitudeArcModel {
  /**
   * Computes the arc altitude based on distance and progress.
   * Uses a parabolic curve where peak scales with distance.
   */
  public static calculateArcAltitude(startAlt: number, endAlt: number, t: number, distanceDegrees: number): number {
    // Linear interpolation base
    const linearAlt = CameraInterpolator.lerp(startAlt, endAlt, t);
    
    // Parabolic arc multiplier: 4 * t * (1 - t) peaks at 1.0 when t=0.5
    const parabola = 4 * t * (1 - t);
    
    // Scale peak based on distance (e.g. up to a max altitude for very long flights)
    // Roughly 100,000 meters per degree of distance as a cinematic heuristic
    const peakAltitude = Math.min(distanceDegrees * 100000, 20000000); 
    
    // Arc contribution
    const arcContribution = peakAltitude * parabola;
    
    return linearAlt + arcContribution;
  }
}
