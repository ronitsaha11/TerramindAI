import type { Vector3 } from '../AtmosphereState';

export interface SkyState {
  zenithColor: [number, number, number];
  horizonColor: [number, number, number];
  ambientIntensity: number;
  twilightFactor: number;
}

export class SkyModel {
  /**
   * Generates a simplified sky state suitable for standard rendering pipelines
   * based on the sun's direction vector relative to the Earth reference frame.
   * 
   * @param sunDirectionEci The normalized direction vector to the Sun.
   * @returns SkyState with colors and intensity
   */
  public generateSkyState(sunDirectionEci: Vector3): SkyState {
    // A simplified model: compute a pseudo-elevation angle based on dot product
    // assuming an observer at a reference point (e.g., [1, 0, 0]).
    // For a globally lit globe, ambient intensity relates to overall scattering.
    
    // In a real celestial model, we'd compute local altitude based on observer position.
    // Here we provide a baseline global approximation.
    const dot = sunDirectionEci.x; // Observer at lat 0, lon 0 approximation
    const twilight = Math.max(0, Math.min(1, (dot + 0.1) * 5)); // 0 = night, 1 = day

    // Base colors (RGB)
    const dayZenith: [number, number, number] = [30, 80, 160];
    const dayHorizon: [number, number, number] = [180, 200, 220];
    const nightZenith: [number, number, number] = [2, 5, 15];
    const nightHorizon: [number, number, number] = [10, 15, 30];

    return {
      zenithColor: [
        this.lerp(nightZenith[0], dayZenith[0], twilight),
        this.lerp(nightZenith[1], dayZenith[1], twilight),
        this.lerp(nightZenith[2], dayZenith[2], twilight)
      ],
      horizonColor: [
        this.lerp(nightHorizon[0], dayHorizon[0], twilight),
        this.lerp(nightHorizon[1], dayHorizon[1], twilight),
        this.lerp(nightHorizon[2], dayHorizon[2], twilight)
      ],
      ambientIntensity: Math.max(0.05, twilight * 1.5),
      twilightFactor: twilight
    };
  }

  private lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t;
  }
}
