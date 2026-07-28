export interface SimulationConfig {
  /** Initial absolute simulation time in milliseconds (Unix Epoch) */
  initialTimeMs: number;
  /** The starting multiplier (e.g., 1.0 for real-time, 0 for paused) */
  defaultMultiplier: number;
  /** The maximum allowed real-world delta time per tick to prevent spiraling (e.g., after tab backgrounding) */
  maxDeltaMs: number;
}

export const DEFAULT_SIMULATION_CONFIG: SimulationConfig = {
  initialTimeMs: Date.now(), // Fallback, usually overridden by specific scenario
  defaultMultiplier: 1.0,
  maxDeltaMs: 100, // Clamp at 100ms (10fps min) to prevent massive jumps if thread hangs
};
