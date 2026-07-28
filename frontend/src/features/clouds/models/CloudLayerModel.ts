import { CloudValidation } from '../CloudValidation';

export class CloudLayerModel {
  private enabled: boolean = true;
  private altitudeMeters: number;
  private opacity: number;

  constructor(altitudeMeters: number, opacity: number) {
    CloudValidation.validateAltitude(altitudeMeters);
    CloudValidation.validateOpacity(opacity);
    this.altitudeMeters = altitudeMeters;
    this.opacity = opacity;
  }

  public getAltitudeMeters(): number {
    return this.altitudeMeters;
  }

  public getOpacity(): number {
    return this.opacity;
  }

  public isEnabled(): boolean {
    return this.enabled;
  }

  public setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  public setOpacity(opacity: number): void {
    CloudValidation.validateOpacity(opacity);
    this.opacity = opacity;
  }

  public setAltitude(altitudeMeters: number): void {
    CloudValidation.validateAltitude(altitudeMeters);
    this.altitudeMeters = altitudeMeters;
  }
}
