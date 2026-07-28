import type { IDataset } from '../models/dataset';

/**
 * Responsible for importing raw external data and transforming it into an immutable Dataset domain object.
 * Ownership: Translates external formats to internal representations.
 */
export interface IDatasetImporter<TRawInput, TParsedData> {
  /**
   * Imports raw data and returns a dataset domain object.
   * 
   * @param input - The raw data to import.
   * @param name - The name to assign to the dataset.
   * @returns A promise resolving to the created dataset.
   */
  import(input: TRawInput, name: string): Promise<IDataset<TParsedData>>;
}
