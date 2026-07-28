export type FidelityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'ULTRA';

export interface IPerformanceState {
  rollingFps: number;
  fidelityLevel: FidelityLevel;
  throttling: boolean;
  lastAdjustmentTime: number;
}
