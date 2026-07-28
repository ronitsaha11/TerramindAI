import type { IDataset } from '../models/dataset';
import type { IDatasetRegistry } from '../registry/dataset-registry.interface';

/**
 * State representing the reactive mirror of the Dataset Registry and UI-specific dataset state.
 * Ownership: UI/Application state. Mirrored datasets.
 */
export interface DatasetStoreState {
  /**
   * A readonly dictionary of datasets, keyed by their ID.
   */
  datasets: Readonly<Record<string, IDataset>>;

  /**
   * An ordered list of dataset IDs, preserving registry insertion order.
   */
  datasetIds: readonly string[];

  /**
   * The ID of the currently active/selected dataset in the UI, if any.
   */
  activeDatasetId: string | null;

  /**
   * Indicates whether the store has been initialized and synchronized with the registry.
   */
  initialized: boolean;

  /**
   * Indicates whether the store is currently performing a synchronization pass.
   */
  syncing: boolean;
}

/**
 * Public actions exposed by the Dataset Store.
 * Does NOT include mutation actions like `registerDataset` (which belong to the Registry).
 */
export interface DatasetStoreActions {
  /**
   * Initializes the store by synchronizing with the provided DatasetRegistry
   * and subscribing to its changes. Prevents duplicate initialization.
   * 
   * @param registry - The authoritative Dataset Registry instance to mirror.
   */
  initialize(registry: IDatasetRegistry): void;

  /**
   * Sets the active dataset for the UI context.
   * 
   * @param id - The ID of the dataset to activate.
   */
  setActiveDataset(id: string): void;

  /**
   * Clears the currently active dataset.
   */
  clearActiveDataset(): void;

  /**
   * Optional cleanup function for HMR or graceful shutdown.
   */
  destroy(): void;
}

export type DatasetStore = DatasetStoreState & DatasetStoreActions;
