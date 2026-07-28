import type { EarthState } from './PlanetTypes';

export type EarthStateListener = (state: Readonly<EarthState>) => void;

/**
 * Lightweight domain-local event emitter for the Earth Ephemeris.
 */
export class EphemerisEvents {
  private updateListeners: EarthStateListener[] = [];

  public onUpdated(listener: EarthStateListener): () => void {
    this.updateListeners.push(listener);
    return () => this.removeListener(this.updateListeners, listener);
  }

  public dispatchUpdated(state: Readonly<EarthState>): void {
    for (let i = 0; i < this.updateListeners.length; i++) {
      this.updateListeners[i](state);
    }
  }

  private removeListener<T>(arr: T[], listener: T): void {
    const idx = arr.indexOf(listener);
    if (idx !== -1) {
      arr.splice(idx, 1);
    }
  }
}
