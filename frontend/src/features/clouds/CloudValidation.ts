export class CloudValidation {
  public static validateAltitude(altitudeMeters: number): void {
    if (altitudeMeters < 0 || altitudeMeters > 50000) {
      throw new Error(`[CloudValidation] Cloud altitude ${altitudeMeters} is out of realistic physical bounds.`);
    }
  }

  public static validateOpacity(opacity: number): void {
    if (opacity < 0 || opacity > 1) {
      throw new Error(`[CloudValidation] Cloud opacity ${opacity} must be between 0 and 1.`);
    }
  }
}
