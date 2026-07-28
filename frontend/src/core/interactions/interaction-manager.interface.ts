import type { IFeature, InteractionState, InteractionChangeListener } from './interaction.types';

/**
 * The canonical source of truth for all interaction state (hover, selection)
 * throughout the Earth Intelligence Platform.
 * 
 * It operates strictly as a native publish-subscribe domain module,
 * completely decoupled from any UI framework or rendering engine.
 */
export interface IInteractionManager {
  /**
   * Sets the currently hovered feature and cursor coordinates.
   * 
   * @param feature - The feature being hovered, or null to clear hover on a specific coordinate change.
   * @param cursorX - The X pixel coordinate of the cursor.
   * @param cursorY - The Y pixel coordinate of the cursor.
   */
  setHovered(feature: IFeature | null, cursorX: number | null, cursorY: number | null): void;

  /**
   * Sets the currently selected feature.
   * Replaces any existing selection (single-selection model).
   * 
   * @param feature - The feature to select, or null to clear selection.
   */
  setSelected(feature: IFeature | null): void;

  /**
   * Clears the current hover state, including cursor coordinates.
   */
  clearHover(): void;

  /**
   * Clears the current selection state.
   */
  clearSelection(): void;

  /**
   * Clears all interaction state (both hover and selection).
   */
  clearAll(): void;

  /**
   * Returns an immutable snapshot of the current interaction state.
   * 
   * @returns The current InteractionState.
   */
  getState(): Readonly<InteractionState>;

  /**
   * Subscribes a listener to interaction state changes.
   * 
   * @param listener - The callback to invoke when state changes.
   * @returns A function to unsubscribe this specific listener.
   */
  subscribe(listener: InteractionChangeListener): () => void;

  /**
   * Explicitly unsubscribes a previously registered listener.
   * 
   * @param listener - The callback to remove.
   */
  unsubscribe(listener: InteractionChangeListener): void;
}
