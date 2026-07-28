import { PERFORMANCE_CONFIG } from '../PerformanceConfig';

export class RollingAverageModel {
  private currentEma: number = PERFORMANCE_CONFIG.targetFps;

  public update(instantFps: number): number {
    this.currentEma = (instantFps * PERFORMANCE_CONFIG.emaAlpha) + (this.currentEma * (1 - PERFORMANCE_CONFIG.emaAlpha));
    return this.currentEma;
  }

  public getAverage(): number {
    return this.currentEma;
  }
}
