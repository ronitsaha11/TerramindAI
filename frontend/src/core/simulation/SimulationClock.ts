import { SimulationEvents } from './SimulationEvents';
import { DEFAULT_SIMULATION_CONFIG, type SimulationConfig } from './SimulationConfig';
import type { ISimulationClock, SimulationState } from './SimulationTypes';

export class SimulationClock implements ISimulationClock {
  public readonly events: SimulationEvents;
  
  private readonly config: SimulationConfig;
  
  // Single allocated state object to prevent per-frame heap allocations
  private readonly _state: SimulationState;

  // Track if we've started to emit the 'Started' event on first tick
  private _hasStarted: boolean = false;

  constructor(config: Partial<SimulationConfig> = {}) {
    this.config = { ...DEFAULT_SIMULATION_CONFIG, ...config };
    this.events = new SimulationEvents();
    
    this._state = {
      timeMs: this.config.initialTimeMs,
      deltaMs: 0,
      multiplier: this.config.defaultMultiplier,
      isPaused: false,
    };
  }

  public tick(realWorldDeltaMs: number): void {
    if (!this._hasStarted) {
      this._hasStarted = true;
      this.events.dispatchStarted();
    }

    if (this._state.isPaused) {
      this._state.deltaMs = 0;
      this.events.dispatchTick(this._state);
      return;
    }

    // Clamp the delta to prevent massive time jumps if the main thread hung
    const clampedDelta = Math.min(realWorldDeltaMs, this.config.maxDeltaMs);
    
    // Apply multiplier
    const simDelta = clampedDelta * this._state.multiplier;
    
    this._state.deltaMs = simDelta;
    this._state.timeMs += simDelta;

    this.events.dispatchTick(this._state);
  }

  public pause(): void {
    if (this._state.isPaused) return;
    this._state.isPaused = true;
    this.events.dispatchPaused();
  }

  public resume(): void {
    if (!this._state.isPaused) return;
    this._state.isPaused = false;
    this.events.dispatchResumed();
  }

  public togglePause(): void {
    if (this._state.isPaused) {
      this.resume();
    } else {
      this.pause();
    }
  }

  public setMultiplier(multiplier: number): void {
    if (multiplier < 0) {
      console.warn('[SimulationClock] Negative multipliers are not supported. Clamping to 0.');
      multiplier = 0;
    }
    
    if (this._state.multiplier === multiplier) return;
    
    this._state.multiplier = multiplier;
    this.events.dispatchSpeedChanged();
  }

  public reset(): void {
    this._state.timeMs = this.config.initialTimeMs;
    this._state.deltaMs = 0;
    this._state.multiplier = this.config.defaultMultiplier;
    this._state.isPaused = false;
    this.events.dispatchReset();
    
    // Emit one tick to push the reset state to subscribers immediately
    this.events.dispatchTick(this._state);
  }

  public getState(): Readonly<SimulationState> {
    return this._state;
  }
}
