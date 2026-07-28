import type { InteractionState } from '../../../core/interactions/interaction.types';

/**
 * Zustand store state for Interactions.
 * 
 * Note: This store is strictly a synchronized projection of the core domain
 * InteractionManager. It does NOT own the interaction state and exposes NO mutators
 * other than synchronization methods for the InteractionBridge.
 */
export interface InteractionStoreState extends InteractionState {
  /** Whether the store has received its initial sync from the manager. */
  readonly initialized: boolean;

  /** Strictly for use by the InteractionBridge to sync the domain state. */
  setSnapshot(snapshot: Readonly<InteractionState>): void;
  
  /** Strictly for use by the InteractionBridge. */
  setInitialized(initialized: boolean): void;
}
