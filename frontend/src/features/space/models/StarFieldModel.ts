import type { StarConfig } from '../SpaceTypes';

export class StarFieldModel {
  private visibility: boolean;
  private intensity: number;

  constructor(visibility: boolean, intensity: number) {
    this.visibility = visibility;
    this.intensity = intensity;
  }

  public getConfig(): StarConfig {
    return {
      visibility: this.visibility,
      intensity: this.intensity
    };
  }
}
