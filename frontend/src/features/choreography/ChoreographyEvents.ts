import type { IChoreographyState } from './ChoreographyState';

type EventCallback<T> = (data: T) => void;

export class ChoreographyEvents {
  private onStateUpdatedHandlers: Set<EventCallback<IChoreographyState>> = new Set();

  public onStateUpdated(handler: EventCallback<IChoreographyState>): () => void {
    this.onStateUpdatedHandlers.add(handler);
    return () => this.onStateUpdatedHandlers.delete(handler);
  }

  public emitStateUpdated(state: IChoreographyState): void {
    this.onStateUpdatedHandlers.forEach(h => h(state));
  }
}
