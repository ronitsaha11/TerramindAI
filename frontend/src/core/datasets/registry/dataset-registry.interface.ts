import type { IDataset } from '../models/dataset';
import type { DatasetStyle } from '../../styles/style.types';

/**
 * Listener type for dataset registry change notifications.
 */
export type RegistryChangeListener = () => void;

/**
 * Interface representing the Dataset Registry.
 * Acts as the single source of truth for all datasets in TerraMind AI.
 * Owns the instances and lifecycle of datasets, but knows nothing about rendering or UI state.
 */
export interface IDatasetRegistry {
  /**
   * Registers a dataset in the registry.
   * Throws an error if a dataset with the same ID already exists.
   * 
   * @param dataset - The dataset to register.
   * @throws DuplicateDatasetError if the dataset ID is already registered.
   */
  register(dataset: IDataset): void;

  /**
   * Unregisters a dataset from the registry by its ID.
   * Throws an error if the dataset does not exist.
   * 
   * @param id - The ID of the dataset to unregister.
   * @throws DatasetNotFoundError if the dataset is not found in the registry.
   */
  unregister(id: string): void;

  /**
   * Updates the style configuration of an existing dataset.
   * Clones the dataset to maintain immutability and notifies subscribers.
   * 
   * @param datasetId - The ID of the dataset to update.
   * @param style - The new style configuration.
   * @throws DatasetNotFoundError if the dataset is not found in the registry.
   */
  updateStyle(datasetId: string, style: DatasetStyle): void;

  /**
   * Retrieves a dataset by its ID.
   * 
   * @param id - The ID of the dataset to retrieve.
   * @returns The dataset, or undefined if it does not exist.
   */
  get(id: string): IDataset | undefined;

  /**
   * Checks if a dataset with the given ID exists in the registry.
   * 
   * @param id - The ID of the dataset to check.
   * @returns True if the dataset exists, false otherwise.
   */
  has(id: string): boolean;

  /**
   * Returns a readonly list of all registered datasets.
   * Preserves insertion order.
   * 
   * @returns A readonly array of datasets.
   */
  list(): ReadonlyArray<IDataset>;

  /**
   * Returns the total number of datasets currently registered.
   * 
   * @returns The count of datasets.
   */
  count(): number;

  /**
   * Clears all datasets from the registry.
   */
  clear(): void;

  /**
   * Subscribes a listener to registry change events.
   * The listener is invoked whenever a dataset is registered, unregistered, or the registry is cleared.
   * 
   * @param listener - The function to invoke on changes.
   * @returns A function that can be called to unsubscribe the listener.
   */
  subscribe(listener: RegistryChangeListener): () => void;

  /**
   * Unsubscribes a listener from registry change events.
   * 
   * @param listener - The function to remove.
   */
  unsubscribe(listener: RegistryChangeListener): void;
}
