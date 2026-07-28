import type { SimulationState } from '../../../core/simulation/SimulationTypes';

export interface SimulationStoreState {
  timeMs: number;
  multiplier: number;
  isPaused: boolean;
  initialized: boolean;
  
  setSnapshot: (snapshot: Readonly<SimulationState>) => void;
  setInitialized: (initialized: boolean) => void;
}
