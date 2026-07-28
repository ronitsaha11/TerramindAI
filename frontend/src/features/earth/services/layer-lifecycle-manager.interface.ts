/**
 * Immutable plan representing the actions required to synchronize
 * rendering layers with desired dataset states.
 */
export interface LayerReconciliationResult {
  /** Array of layer IDs that need to be added/rendered. */
  readonly add: readonly string[];

  /** Array of layer IDs that need to be removed from the renderer. */
  readonly remove: readonly string[];

  /** Array of layer IDs that are already synced and require no changes. */
  readonly keep: readonly string[];
}

/**
 * Manager responsible for owning the synchronized layer state and
 * computing reconciliation plans.
 * 
 * It separates the decision of *what* to synchronize from the actual
 * execution of rendering commands.
 */
export interface ILayerLifecycleManager {
  /**
   * Compares the desired dataset IDs against the currently tracked layer state
   * and computes a reconciliation plan (add, remove, keep).
   * 
   * This method updates the internal tracked state to match the desired IDs.
   * 
   * @param desiredIds - The IDs of the datasets that should be rendered.
   * @returns An immutable reconciliation plan.
   */
  reconcile(desiredIds: readonly string[]): LayerReconciliationResult;
}
