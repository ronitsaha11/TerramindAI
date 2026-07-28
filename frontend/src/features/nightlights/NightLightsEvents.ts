import type { NightLightsState } from './NightLightsState';

type EventCallback<T> = (data: T) => void;

export class NightLightsEvents {
  private onStateUpdatedHandlers: Set<EventCallback<NightLightsState>> = new Set();

  public onStateUpdated(handler: EventCallback<NightLightsState>): () => void {
    this.onStateUpdatedHandlers.add(handler);
    return () => this.onStateUpdatedHandlers.delete(handler);
  }

  public emitStateUpdated(state: NightLightsState): void {
    this.onStateUpdatedHandlers.forEach(h => h(state));
  }
}
