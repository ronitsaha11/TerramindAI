import type { SimulationState } from './SimulationTypes';

export type SimulationTickListener = (state: Readonly<SimulationState>) => void;
export type SimulationStateListener = () => void;

/**
 * Lightweight domain-local event emitter for the Simulation Clock.
 */
export class SimulationEvents {
  private tickListeners: SimulationTickListener[] = [];
  private startListeners: SimulationStateListener[] = [];
  private pauseListeners: SimulationStateListener[] = [];
  private resumeListeners: SimulationStateListener[] = [];
  private resetListeners: SimulationStateListener[] = [];
  private speedChangedListeners: SimulationStateListener[] = [];

  // Subscriptions
  
  public onTick(listener: SimulationTickListener): () => void {
    this.tickListeners.push(listener);
    return () => this.removeListener(this.tickListeners, listener);
  }

  public onStarted(listener: SimulationStateListener): () => void {
    this.startListeners.push(listener);
    return () => this.removeListener(this.startListeners, listener);
  }

  public onPaused(listener: SimulationStateListener): () => void {
    this.pauseListeners.push(listener);
    return () => this.removeListener(this.pauseListeners, listener);
  }

  public onResumed(listener: SimulationStateListener): () => void {
    this.resumeListeners.push(listener);
    return () => this.removeListener(this.resumeListeners, listener);
  }

  public onReset(listener: SimulationStateListener): () => void {
    this.resetListeners.push(listener);
    return () => this.removeListener(this.resetListeners, listener);
  }

  public onSpeedChanged(listener: SimulationStateListener): () => void {
    this.speedChangedListeners.push(listener);
    return () => this.removeListener(this.speedChangedListeners, listener);
  }

  // Dispatches (Internal to domain)

  public dispatchTick(state: Readonly<SimulationState>): void {
    for (let i = 0; i < this.tickListeners.length; i++) {
      this.tickListeners[i](state);
    }
  }

  public dispatchStarted(): void {
    for (let i = 0; i < this.startListeners.length; i++) {
      this.startListeners[i]();
    }
  }

  public dispatchPaused(): void {
    for (let i = 0; i < this.pauseListeners.length; i++) {
      this.pauseListeners[i]();
    }
  }

  public dispatchResumed(): void {
    for (let i = 0; i < this.resumeListeners.length; i++) {
      this.resumeListeners[i]();
    }
  }

  public dispatchReset(): void {
    for (let i = 0; i < this.resetListeners.length; i++) {
      this.resetListeners[i]();
    }
  }

  public dispatchSpeedChanged(): void {
    for (let i = 0; i < this.speedChangedListeners.length; i++) {
      this.speedChangedListeners[i]();
    }
  }

  private removeListener<T>(arr: T[], listener: T): void {
    const idx = arr.indexOf(listener);
    if (idx !== -1) {
      arr.splice(idx, 1);
    }
  }
}
