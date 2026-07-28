import type { AtmosphereState } from './AtmosphereState';

type EventCallback<T> = (data: T) => void;

export class AtmosphereEvents {
  private onStateUpdatedHandlers: Set<EventCallback<AtmosphereState>> = new Set();

  public onStateUpdated(handler: EventCallback<AtmosphereState>): () => void {
    this.onStateUpdatedHandlers.add(handler);
    return () => this.onStateUpdatedHandlers.delete(handler);
  }

  public emitStateUpdated(state: AtmosphereState): void {
    this.onStateUpdatedHandlers.forEach(h => h(state));
  }
}
