/**
 * Immutable shape of the simulation state.
 * Emitted to subscribers on tick.
 */
export interface SimulationState {
  /** Absolute simulation time (Unix Epoch ms) */
  timeMs: number;
  /** Amount of simulation time that passed this tick (can be negative if reversing) */
  deltaMs: number;
  /** Current time multiplier */
  multiplier: number;
  /** Whether the simulation is currently paused */
  isPaused: boolean;
}

import type { SimulationEvents } from './SimulationEvents';

export interface ISimulationClock {
  readonly events: SimulationEvents;

  /** Advances the simulation by a real-world delta time */
  tick(realWorldDeltaMs: number): void;
  
  /** Pauses the simulation progression */
  pause(): void;
  
  /** Resumes the simulation progression */
  resume(): void;
  
  /** Toggles between pause and resume */
  togglePause(): void;
  
  /** Sets the simulation speed multiplier. Must be positive in this implementation per requirements. */
  setMultiplier(multiplier: number): void;
  
  /** Resets the clock to the initial configuration */
  reset(): void;
  
  /** Returns the current state (read-only reference) */
  getState(): Readonly<SimulationState>;
}
