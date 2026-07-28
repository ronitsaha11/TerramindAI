import { PERFORMANCE_CONFIG } from '../PerformanceConfig';

export class HysteresisModel {
  private lastAdjustmentTime: number = 0;

  public canAdjust(currentTime: number): boolean {
    if (this.lastAdjustmentTime === 0) {
      // First adjustment is always allowed
      return true;
    }
    
    return (currentTime - this.lastAdjustmentTime) > PERFORMANCE_CONFIG.hysteresisCooldownMs;
  }

  public recordAdjustment(currentTime: number): void {
    this.lastAdjustmentTime = currentTime;
  }
}
