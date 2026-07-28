/**
 * Controller responsible for synchronizing datasets from the Dataset Registry
 * to the LayerManager via the DatasetLayerFactory.
 *
 * It listens to registry changes (add, remove, clear) and ensures the rendering engine
 * reflects the correct dataset layers.
 */
export interface IDatasetLayerController {
  /**
   * Initializes the controller, performing an initial sync and subscribing to the registry.
   * Can only be called once safely.
   */
  initialize(): void;

  /**
   * Destroys the controller, unsubscribing from the registry and cleaning up resources.
   * Safe to call on unmount (React Strict Mode compatibility).
   */
  destroy(): void;
}
