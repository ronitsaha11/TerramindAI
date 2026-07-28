export class CloudMovementModel {
  private baseSpeedDegreesPerSecond: number;
  private currentOffsetDegrees: number = 0;

  constructor(baseSpeedDegreesPerSecond: number) {
    this.baseSpeedDegreesPerSecond = baseSpeedDegreesPerSecond;
  }

  /**
   * Deterministically updates the rotation offset based on elapsed time.
   * @param dtSeconds Delta time in seconds
   * @param speedMultiplier Multiplier (e.g. from simulation clock speed)
   */
  public update(dtSeconds: number, speedMultiplier: number = 1.0): void {
    const delta = this.baseSpeedDegreesPerSecond * dtSeconds * speedMultiplier;
    this.currentOffsetDegrees = (this.currentOffsetDegrees + delta) % 360;
  }

  public getOffsetDegrees(): number {
    return this.currentOffsetDegrees;
  }
}
