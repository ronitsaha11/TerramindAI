/**
 * Base error for all spatial query issues.
 */
export class SpatialError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SpatialError';
    Object.setPrototypeOf(this, SpatialError.prototype);
  }
}

/**
 * Thrown when an error occurs during the execution of a spatial query.
 */
export class SpatialQueryError extends SpatialError {
  constructor(message: string) {
    super(message);
    this.name = 'SpatialQueryError';
    Object.setPrototypeOf(this, SpatialQueryError.prototype);
  }
}

/**
 * Thrown when an invalid geometry is provided or encountered during evaluation.
 */
export class InvalidGeometryError extends SpatialError {
  constructor(message: string) {
    super(message);
    this.name = 'InvalidGeometryError';
    Object.setPrototypeOf(this, InvalidGeometryError.prototype);
  }
}

/**
 * Thrown when an invalid bounding box is provided.
 */
export class InvalidBoundingBoxError extends SpatialError {
  constructor(message: string) {
    super(message);
    this.name = 'InvalidBoundingBoxError';
    Object.setPrototypeOf(this, InvalidBoundingBoxError.prototype);
  }
}
