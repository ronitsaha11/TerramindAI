import type { IFlightParameters } from './ChoreographyTypes';

export class ChoreographyValidation {
  public static validateFlightParams(params: IFlightParameters): void {
    if (params.durationMs <= 0) {
      throw new Error(`[ChoreographyValidation] durationMs must be > 0. Got: ${params.durationMs}`);
    }
    if (params.targetLatitude < -90 || params.targetLatitude > 90) {
      throw new Error(`[ChoreographyValidation] targetLatitude out of bounds. Got: ${params.targetLatitude}`);
    }
  }
}
