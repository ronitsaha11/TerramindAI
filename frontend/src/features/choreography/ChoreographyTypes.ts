export type ChoreographyStatus = 'idle' | 'animating' | 'interrupted';
export type InterruptionReason = 'USER_INPUT' | 'NEW_SEQUENCE' | 'ENGINE_RESET' | 'NONE';

export interface IFlightParameters {
  targetLatitude: number;
  targetLongitude: number;
  targetAltitude?: number;
  targetBearing?: number;
  targetPitch?: number;
  
  durationMs: number;
  arcEnabled: boolean;
  
  // Custom easing function identifier or reference
  easing?: string;
  
  startClockRate?: number;
  targetClockRate?: number;
  restoreClockRate?: boolean;
}
