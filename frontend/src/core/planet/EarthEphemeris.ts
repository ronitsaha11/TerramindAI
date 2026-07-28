import type { ISimulationClock, SimulationState } from '../simulation';
import type { EarthState } from './PlanetTypes';
import { EphemerisEvents } from './EphemerisEvents';
import { 
  J2000_EPOCH_MS, 
  MS_PER_DAY, 
  ERA_CONSTANT_DEGREES, 
  ERA_RATE_DEGREES_PER_DAY 
} from './EphemerisConstants';

/**
 * The EarthEphemeris is the canonical provider of the Earth's rotational state.
 * It derives its state exclusively from the Simulation Clock.
 */
export class EarthEphemeris {
  public readonly events: EphemerisEvents;
  
  // Internal zero-allocation state object
  private readonly _state: EarthState;
  
  private unsubscribeTick: (() => void) | null = null;
  private unsubscribeReset: (() => void) | null = null;
  private readonly clock: ISimulationClock;

  constructor(clock: ISimulationClock) {
    this.clock = clock;
    this.events = new EphemerisEvents();
    
    // Initialize state to 0, then immediately compute based on current clock state
    this._state = {
      daysSinceJ2000: 0,
      rotationAngleDegrees: 0
    };
    
    this.updateState(this.clock.getState());
    
    // Subscribe to clock updates
    this.unsubscribeTick = this.clock.events.onTick((simState) => {
      this.updateState(simState);
    });
    
    this.unsubscribeReset = this.clock.events.onReset(() => {
      this.updateState(this.clock.getState());
    });
  }

  /**
   * Updates the internal state in place to avoid steady-state heap allocations.
   */
  private updateState(simState: Readonly<SimulationState>): void {
    // 1. Calculate continuous days since J2000
    const msSinceJ2000 = simState.timeMs - J2000_EPOCH_MS;
    const daysSinceJ2000 = msSinceJ2000 / MS_PER_DAY;
    
    // 2. Compute Earth Rotation Angle (ERA)
    // Formula: ERA = 280.46061837504 + 360.9856122880876 * d
    // We normalize to [0, 360).
    const rawAngle = ERA_CONSTANT_DEGREES + (ERA_RATE_DEGREES_PER_DAY * daysSinceJ2000);
    
    // Normalize safely taking modulo for negative values as well
    const normalizedAngle = ((rawAngle % 360) + 360) % 360;

    // Mutate internal state
    this._state.daysSinceJ2000 = daysSinceJ2000;
    this._state.rotationAngleDegrees = normalizedAngle;

    // Dispatch update to subscribers
    this.events.dispatchUpdated(this._state);
  }

  /**
   * Returns a read-only reference to the current Earth state.
   */
  public getState(): Readonly<EarthState> {
    return this._state;
  }

  /**
   * Cleans up subscriptions to the SimulationClock.
   */
  public destroy(): void {
    if (this.unsubscribeTick) {
      this.unsubscribeTick();
      this.unsubscribeTick = null;
    }
    if (this.unsubscribeReset) {
      this.unsubscribeReset();
      this.unsubscribeReset = null;
    }
  }
}
