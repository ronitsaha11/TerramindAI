import type { IPerformanceState } from './PerformanceTypes';
import type { PerformanceProfile } from './PerformanceProfile';

type EventCallback<T> = (data: T) => void;

export class PerformanceEvents {
  private onStateUpdatedHandlers: Set<EventCallback<IPerformanceState>> = new Set();
  private onProfileUpdatedHandlers: Set<EventCallback<PerformanceProfile>> = new Set();

  public onStateUpdated(handler: EventCallback<IPerformanceState>): () => void {
    this.onStateUpdatedHandlers.add(handler);
    return () => this.onStateUpdatedHandlers.delete(handler);
  }

  public emitStateUpdated(state: IPerformanceState): void {
    this.onStateUpdatedHandlers.forEach(h => h(state));
  }
  
  public onProfileUpdated(handler: EventCallback<PerformanceProfile>): () => void {
    this.onProfileUpdatedHandlers.add(handler);
    return () => this.onProfileUpdatedHandlers.delete(handler);
  }
  
  public emitProfileUpdated(profile: PerformanceProfile): void {
    this.onProfileUpdatedHandlers.forEach(h => h(profile));
  }
}
