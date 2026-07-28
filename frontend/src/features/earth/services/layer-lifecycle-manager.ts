import type { ILayerLifecycleManager, LayerReconciliationResult } from './layer-lifecycle-manager.interface';

/**
 * Implementation of the LayerLifecycleManager.
 * Owns the synchronization state and computes deterministic rendering updates.
 */
export class LayerLifecycleManager implements ILayerLifecycleManager {
  /**
   * Tracks the IDs of dataset layers that have been synchronized to the renderer.
   */
  private synchronizedLayerIds: Set<string>;

  constructor() {
    this.synchronizedLayerIds = new Set<string>();
  }

  public reconcile(desiredIds: readonly string[]): LayerReconciliationResult {
    const desiredSet = new Set(desiredIds);
    const add: string[] = [];
    const remove: string[] = [];
    const keep: string[] = [];

    // 1. Determine what to add or keep
    for (const id of desiredIds) {
      if (this.synchronizedLayerIds.has(id)) {
        keep.push(id);
      } else {
        add.push(id);
      }
    }

    // 2. Determine what to remove
    for (const id of this.synchronizedLayerIds) {
      if (!desiredSet.has(id)) {
        remove.push(id);
      }
    }

    // 3. Update the internal synchronized state to reflect the new desired state
    this.synchronizedLayerIds = desiredSet;

    // 4. Return the immutable plan
    return {
      add: Object.freeze(add),
      remove: Object.freeze(remove),
      keep: Object.freeze(keep),
    };
  }
}
