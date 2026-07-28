import type { TwilightAttenuation } from './NightLightsTypes';

export class NightLightsValidation {
  public static validateIntensity(intensity: number): void {
    if (intensity < 0) {
      throw new Error(`[NightLightsValidation] Intensity ${intensity} must be positive.`);
    }
  }

  public static validateAttenuation(attenuation: TwilightAttenuation): void {
    if (attenuation.start <= attenuation.end) {
      throw new Error(`[NightLightsValidation] Twilight start (${attenuation.start}) must be greater than end (${attenuation.end}).`);
    }
  }
}
