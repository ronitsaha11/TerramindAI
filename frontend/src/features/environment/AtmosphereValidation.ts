export class AtmosphereValidation {
  public static validateRadii(planetRadius: number, atmosphereRadius: number): void {
    if (planetRadius <= 0) {
      throw new Error(`[AtmosphereValidation] Planet radius must be positive.`);
    }
    if (atmosphereRadius <= planetRadius) {
      throw new Error(`[AtmosphereValidation] Atmosphere radius must be strictly greater than planet radius.`);
    }
  }

  public static validateScaleHeight(scaleHeight: number): void {
    if (scaleHeight <= 0) {
      throw new Error(`[AtmosphereValidation] Scale height must be positive.`);
    }
  }
}
