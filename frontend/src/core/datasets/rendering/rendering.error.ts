import { DatasetError } from '../errors/dataset.error';

/**
 * Base error for all rendering-related dataset issues.
 */
export class RenderingError extends DatasetError {
  constructor(message: string) {
    super(message);
    this.name = 'RenderingError';
  }
}

/**
 * Thrown when a dataset type is not supported by the dataset layer factory or renderer.
 */
export class UnsupportedDatasetTypeError extends RenderingError {
  constructor(message: string) {
    super(message);
    this.name = 'UnsupportedDatasetTypeError';
  }
}
