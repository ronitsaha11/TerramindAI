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
