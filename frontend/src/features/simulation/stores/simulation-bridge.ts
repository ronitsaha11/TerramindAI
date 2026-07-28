import type { ISimulationClock } from '../../../core/simulation/SimulationTypes';
import { useSimulationStore } from './use-simulation-store';

/**
 * The SimulationBridge connects the domain SimulationClock to the React Zustand store.
 * 
 * Responsibilities:
 * - Subscribes to the SimulationClock.
 * - Receives immutable state snapshots (or references we treat as immutable).
 * - Forwards those snapshots to the Zustand projection.
 * - Throttles UI updates to avoid 60FPS React renders where possible.
 */
export class SimulationBridge {
  private readonly clock: ISimulationClock;
  private unsubscribeTick: (() => void) | null = null;
  private unsubscribeSpeed: (() => void) | null = null;
  private unsubscribePause: (() => void) | null = null;
  private unsubscribeResume: (() => void) | null = null;
  private unsubscribeReset: (() => void) | null = null;
  private isInitialized = false;

  // Throttle tick updates to UI (e.g. max 10 times a second for the UI clock)
  private lastUpdateMs = 0;
  private readonly UI_UPDATE_THROTTLE_MS = 100; 

  constructor(clock: ISimulationClock) {
    this.clock = clock;
  }

  public initialize(): void {
    if (this.isInitialized) return;

    const store = useSimulationStore.getState();

    // 1. Initial sync
    const initialState = this.clock.getState();
    store.setSnapshot(initialState);
    store.setInitialized(true);
    this.lastUpdateMs = performance.now();

    // 2. Subscribe to domain changes
    
    // We throttle the tick so we don't spam React with 60FPS updates.
    // The visual rendering of the planet and simulation logic use the clock domain directly.
    this.unsubscribeTick = this.clock.events.onTick((snapshot) => {
      const now = performance.now();
      if (now - this.lastUpdateMs >= this.UI_UPDATE_THROTTLE_MS) {
        useSimulationStore.getState().setSnapshot(snapshot);
        this.lastUpdateMs = now;
      }
    });

    // For absolute state changes, we bypass throttle and force sync immediately
    const forceSync = () => {
      useSimulationStore.getState().setSnapshot(this.clock.getState());
      this.lastUpdateMs = performance.now();
    };

    this.unsubscribeSpeed = this.clock.events.onSpeedChanged(forceSync);
    this.unsubscribePause = this.clock.events.onPaused(forceSync);
    this.unsubscribeResume = this.clock.events.onResumed(forceSync);
    this.unsubscribeReset = this.clock.events.onReset(forceSync);

    this.isInitialized = true;
  }

  public destroy(): void {
    if (this.unsubscribeTick) this.unsubscribeTick();
    if (this.unsubscribeSpeed) this.unsubscribeSpeed();
    if (this.unsubscribePause) this.unsubscribePause();
    if (this.unsubscribeResume) this.unsubscribeResume();
    if (this.unsubscribeReset) this.unsubscribeReset();

    this.unsubscribeTick = null;
    this.unsubscribeSpeed = null;
    this.unsubscribePause = null;
    this.unsubscribeResume = null;
    this.unsubscribeReset = null;
    
    useSimulationStore.getState().setInitialized(false);
    this.isInitialized = false;
  }
}
