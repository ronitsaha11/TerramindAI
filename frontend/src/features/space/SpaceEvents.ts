import type { SpaceState } from './SpaceState';

type EventCallback<T> = (data: T) => void;

export class SpaceEvents {
  private onStateUpdatedHandlers: Set<EventCallback<SpaceState>> = new Set();

  public onStateUpdated(handler: EventCallback<SpaceState>): () => void {
    this.onStateUpdatedHandlers.add(handler);
    return () => this.onStateUpdatedHandlers.delete(handler);
  }

  public emitStateUpdated(state: SpaceState): void {
    this.onStateUpdatedHandlers.forEach(h => h(state));
  }
}
