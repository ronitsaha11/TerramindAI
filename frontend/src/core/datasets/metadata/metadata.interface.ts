/**
 * Represents metadata associated with a dataset.
 * This is an extensible interface designed to hold information about the dataset.
 */
export interface IDatasetMetadata {
  /**
   * Optional URL where the source data originated.
   */
  sourceUrl?: string;

  /**
   * Optional attribution or copyright information.
   */
  attribution?: string;

  /**
   * Optional spatial bounds of the dataset (e.g., [minX, minY, maxX, maxY]).
   */
  bounds?: [number, number, number, number];

  /**
   * Optional count of features or items in the dataset.
   */
  featureCount?: number;

  /**
   * Optional size of the dataset in bytes.
   */
  sizeInBytes?: number;

  /**
   * Optional custom properties for extensibility.
   */
  customProps?: Record<string, unknown>;
}
