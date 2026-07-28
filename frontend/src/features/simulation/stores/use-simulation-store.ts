import { create } from 'zustand';
import type { SimulationStoreState } from './simulation-store.types';
import type { SimulationState } from '../../../core/simulation/SimulationTypes';

/**
 * Zustand projection of the immutable simulation domain state.
 * 
 * Do NOT attempt to mutate state here.
 * All mutations MUST go through the domain SimulationClock.
 */
export const useSimulationStore = create<SimulationStoreState>((set) => ({
  timeMs: Date.now(), // Fallback, will be immediately overwritten by bridge
  multiplier: 1.0,
  isPaused: false,
  initialized: false,

  setSnapshot: (snapshot: Readonly<SimulationState>) => {
    set({
      timeMs: snapshot.timeMs,
      multiplier: snapshot.multiplier,
      isPaused: snapshot.isPaused,
    });
  },

  setInitialized: (initialized: boolean) => {
    set({ initialized });
  },
}));
