import type { ChoreographyStatus, InterruptionReason, IFlightParameters } from './ChoreographyTypes';

export interface IChoreographyState {
  status: ChoreographyStatus;
  activeFlight: IFlightParameters | null;
  progress: number;
  elapsedTime: number;
  interruptionReason: InterruptionReason;
}
