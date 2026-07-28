import type { CelestialVector } from '../SpaceTypes';

export class MoonVisualModel {
  private positionEci: CelestialVector = { x: 0, y: 1, z: 0 };
  private phase: number = 0;

  public update(positionEci: CelestialVector, phase: number): void {
    this.positionEci = { ...positionEci };
    this.phase = phase;
  }

  public getPositionEci(): CelestialVector {
    return this.positionEci;
  }

  public getPhase(): number {
    return this.phase;
  }
}
