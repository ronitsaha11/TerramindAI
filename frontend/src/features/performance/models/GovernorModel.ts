import type { FidelityLevel } from '../PerformanceTypes';
import { PERFORMANCE_CONFIG } from '../PerformanceConfig';

export class GovernorModel {
  private readonly levels: FidelityLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'ULTRA'];

  public evaluate(currentLevel: FidelityLevel, rollingFps: number): FidelityLevel {
    const currentIndex = this.levels.indexOf(currentLevel);

    if (rollingFps < PERFORMANCE_CONFIG.downgradeFpsThreshold) {
      if (currentIndex > 0) {
        return this.levels[currentIndex - 1];
      }
    } else if (rollingFps > PERFORMANCE_CONFIG.upgradeFpsThreshold) {
      if (currentIndex < this.levels.length - 1) {
        return this.levels[currentIndex + 1];
      }
    }

    return currentLevel;
  }
}
