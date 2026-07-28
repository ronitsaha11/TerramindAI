import type { IDataset } from '../models/dataset';
import type { DatasetLayerDefinition } from './dataset-layer-definition.ts';

/**
 * Responsible for translating immutable IDataset objects into renderer-agnostic
 * DatasetLayerDefinition objects. 
 * Ownership: Operates strictly as a translation layer. It does not instantiate rendering objects.
 */
export interface IDatasetLayerFactory {
  /**
   * Creates a layer definition for the given dataset.
   * 
   * @param dataset - The dataset to translate.
   * @returns The immutable layer definition.
   * @throws UnsupportedDatasetTypeError if the dataset type cannot be translated.
   */
  create(dataset: IDataset): DatasetLayerDefinition;
}
