import type { CelestialVector } from '../SpaceTypes';

export class SunVisualModel {
  private directionEci: CelestialVector = { x: 1, y: 0, z: 0 };

  public update(directionEci: CelestialVector): void {
    this.directionEci = { ...directionEci };
  }

  public getDirectionEci(): CelestialVector {
    return this.directionEci;
  }
}
