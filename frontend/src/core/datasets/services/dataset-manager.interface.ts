import type { IDataset } from '../models/dataset';
import type { IDatasetImporter } from '../contracts/importer.interface';

/**
 * Interface representing the Dataset Manager Service.
 * Acts as the application orchestration layer, coordinating dataset workflows.
 * Owns no datasets itself and performs no direct validation or rendering.
 */
export interface IDatasetManager {
  /**
   * Orchestrates the import of a new dataset using the provided importer.
   * Generates the domain Dataset and registers it in the Registry.
   * 
   * @param importer - The importer responsible for validation, metadata generation, and Dataset construction.
   * @param input - The raw input data to import.
   * @param name - The name to assign to the new dataset.
   * @returns A promise resolving to the fully registered Dataset.
   */
  importDataset<TInput>(
    importer: IDatasetImporter<TInput, unknown>,
    input: TInput,
    name: string
  ): Promise<IDataset>;

  /**
   * Removes a dataset from the application.
   * 
   * @param id - The ID of the dataset to remove.
   */
  removeDataset(id: string): void;

  /**
   * Retrieves a dataset by its ID.
   * 
   * @param id - The ID of the dataset to retrieve.
   * @returns The dataset, or undefined if not found.
   */
  getDataset(id: string): IDataset | undefined;

  /**
   * Retrieves all registered datasets.
   * 
   * @returns A readonly array of all datasets.
   */
  listDatasets(): ReadonlyArray<IDataset>;

  /**
   * Counts the total number of registered datasets.
   * 
   * @returns The dataset count.
   */
  countDatasets(): number;

  /**
   * Checks if a dataset with the given ID exists.
   * 
   * @param id - The ID of the dataset to check.
   * @returns True if the dataset exists, false otherwise.
   */
  hasDataset(id: string): boolean;

  /**
   * Clears all datasets from the application.
   */
  clearDatasets(): void;
}
