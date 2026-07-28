import type { IInteractionManager } from './interaction-manager.interface';
import type { IFeature, InteractionState, InteractionChangeListener } from './interaction.types';

/**
 * Implementation of the InteractionManager.
 * Manages native publish-subscribe state for feature interactions.
 */
export class InteractionManager implements IInteractionManager {
  private state: InteractionState;
  private readonly listeners: Set<InteractionChangeListener>;

  constructor() {
    this.state = Object.freeze({
      hoveredFeature: null,
      selectedFeature: null,
      cursorX: null,
      cursorY: null,
    });
    this.listeners = new Set<InteractionChangeListener>();
  }

  public setHovered(feature: IFeature | null, cursorX: number | null, cursorY: number | null): void {
    this.updateState({
      hoveredFeature: feature ? Object.freeze({ ...feature }) : null,
      cursorX,
      cursorY,
    });
  }

  public setSelected(feature: IFeature | null): void {
    this.updateState({
      selectedFeature: feature ? Object.freeze({ ...feature }) : null,
    });
  }

  public clearHover(): void {
    this.updateState({
      hoveredFeature: null,
      cursorX: null,
      cursorY: null,
    });
  }

  public clearSelection(): void {
    this.updateState({
      selectedFeature: null,
    });
  }

  public clearAll(): void {
    this.updateState({
      hoveredFeature: null,
      selectedFeature: null,
      cursorX: null,
      cursorY: null,
    });
  }

  public getState(): Readonly<InteractionState> {
    return this.state;
  }

  public subscribe(listener: InteractionChangeListener): () => void {
    this.listeners.add(listener);
    return () => this.unsubscribe(listener);
  }

  public unsubscribe(listener: InteractionChangeListener): void {
    this.listeners.delete(listener);
  }

  /**
   * Applies partial updates, freezes a new immutable snapshot, and notifies subscribers synchronously.
   */
  private updateState(updates: Partial<InteractionState>): void {
    const nextState = Object.freeze({
      ...this.state,
      ...updates,
    });

    // Avoid unnecessary notifications if nothing actually changed structurally.
    // Given the strictness, a simple reference check works since we recreate the object, 
    // but in this implementation we always emit. (Could optimize with shallow equal if needed).
    this.state = nextState;
    this.notifySubscribers();
  }

  private notifySubscribers(): void {
    // Notify all listeners synchronously in a try-catch to prevent a failing subscriber from breaking the loop
    for (const listener of this.listeners) {
      try {
        listener(this.state);
      } catch (error) {
        console.error('InteractionManager: Subscriber threw an error during notification', error);
      }
    }
  }
}
