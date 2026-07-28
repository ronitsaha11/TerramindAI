import type { IInteractionManager } from '../../../core/interactions/interaction-manager.interface';
import { useInteractionStore } from './use-interaction-store';

/**
 * The InteractionBridge connects the domain InteractionManager to the React Zustand store.
 * 
 * Responsibilities:
 * - Subscribes to the InteractionManager.
 * - Receives immutable state snapshots.
 * - Forwards those snapshots to the Zustand projection.
 * - Owns the subscription lifecycle (ensures strict mode safety).
 */
export class InteractionBridge {
  private readonly manager: IInteractionManager;
  private unsubscribe: (() => void) | null = null;
  private isInitialized = false;

  constructor(manager: IInteractionManager) {
    this.manager = manager;
  }

  public initialize(): void {
    if (this.isInitialized) return;

    const store = useInteractionStore.getState();

    // 1. Initial sync
    const initialState = this.manager.getState();
    store.setSnapshot(initialState);
    store.setInitialized(true);

    // 2. Subscribe to domain changes
    this.unsubscribe = this.manager.subscribe((snapshot) => {
      useInteractionStore.getState().setSnapshot(snapshot);
    });

    this.isInitialized = true;
  }

  public destroy(): void {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
    
    useInteractionStore.getState().setInitialized(false);
    this.isInitialized = false;
  }
}
