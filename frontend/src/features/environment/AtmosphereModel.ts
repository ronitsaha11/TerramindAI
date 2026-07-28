import { ATMOSPHERE_CONSTANTS } from './AtmosphereConfig';
import { AtmosphereValidation } from './AtmosphereValidation';
import type { Vector3 } from './AtmosphereState';

export class AtmosphereModel {
  private planetRadius: number;
  private atmosphereRadius: number;
  private rayleighScaleHeight: number;
  private mieScaleHeight: number;
  private rayleighScattering: Vector3;
  private mieScattering: number;

  constructor() {
    this.planetRadius = ATMOSPHERE_CONSTANTS.planetRadius;
    this.atmosphereRadius = ATMOSPHERE_CONSTANTS.atmosphereRadius;
    this.rayleighScaleHeight = ATMOSPHERE_CONSTANTS.rayleighScaleHeight;
    this.mieScaleHeight = ATMOSPHERE_CONSTANTS.mieScaleHeight;
    this.rayleighScattering = { ...ATMOSPHERE_CONSTANTS.rayleighScattering };
    this.mieScattering = ATMOSPHERE_CONSTANTS.mieScattering;

    AtmosphereValidation.validateRadii(this.planetRadius, this.atmosphereRadius);
    AtmosphereValidation.validateScaleHeight(this.rayleighScaleHeight);
  }

  // Purely mathematical constants for the renderer to consume
  public getPlanetRadius(): number { return this.planetRadius; }
  public getAtmosphereRadius(): number { return this.atmosphereRadius; }
  public getRayleighScaleHeight(): number { return this.rayleighScaleHeight; }
  public getMieScaleHeight(): number { return this.mieScaleHeight; }
  public getRayleighScattering(): Readonly<Vector3> { return this.rayleighScattering; }
  public getMieScattering(): number { return this.mieScattering; }
}
