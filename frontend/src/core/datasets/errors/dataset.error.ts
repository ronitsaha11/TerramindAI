/**
 * Base class for all dataset-related errors in TerraMind AI.
 * Represents a typed domain error.
 */
export class DatasetError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DatasetError';
    
    // Restore prototype chain for extending Error in TypeScript
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Error thrown when a dataset fails to import from raw input.
 */
export class ImportError extends DatasetError {
  constructor(message: string) {
    super(message);
    this.name = 'ImportError';
  }
}

/**
 * Error thrown when a dataset fails validation checks.
 */
export class ValidationError extends DatasetError {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Error thrown when attempting to register a dataset with an ID that already exists.
 */
export class DuplicateDatasetError extends DatasetError {
  constructor(message: string) {
    super(message);
    this.name = 'DuplicateDatasetError';
  }
}

/**
 * Error thrown when a requested dataset is not found in the registry.
 */
export class DatasetNotFoundError extends DatasetError {
  constructor(message: string) {
    super(message);
    this.name = 'DatasetNotFoundError';
  }
}
