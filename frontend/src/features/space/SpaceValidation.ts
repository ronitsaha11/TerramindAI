export class SpaceValidation {
  public static validateIntensity(intensity: number): void {
    if (intensity < 0 || intensity > 10) {
      throw new Error(`[SpaceValidation] Intensity ${intensity} out of bounds (0-10).`);
    }
  }

  public static validatePhase(phase: number): void {
    if (phase < 0 || phase > 1) {
      throw new Error(`[SpaceValidation] Phase ${phase} must be between 0 and 1.`);
    }
  }
}
