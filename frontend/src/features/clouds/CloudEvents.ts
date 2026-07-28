import type { CloudState } from './CloudState';

type EventCallback<T> = (data: T) => void;

export class CloudEvents {
  private onStateUpdatedHandlers: Set<EventCallback<CloudState>> = new Set();

  public onStateUpdated(handler: EventCallback<CloudState>): () => void {
    this.onStateUpdatedHandlers.add(handler);
    return () => this.onStateUpdatedHandlers.delete(handler);
  }

  public emitStateUpdated(state: CloudState): void {
    this.onStateUpdatedHandlers.forEach(h => h(state));
  }
}
