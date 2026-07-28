/**
 * Base error for all interaction-related issues.
 */
export class InteractionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'InteractionError';
    Object.setPrototypeOf(this, InteractionError.prototype);
  }
}

/**
 * Thrown when an interaction state transitions to an invalid state.
 */
export class InteractionStateError extends InteractionError {
  constructor(message: string) {
    super(message);
    this.name = 'InteractionStateError';
    Object.setPrototypeOf(this, InteractionStateError.prototype);
  }
}

/**
 * Thrown when an invalid interaction is requested (e.g., interacting with a non-existent feature).
 */
export class InvalidInteractionError extends InteractionError {
  constructor(message: string) {
    super(message);
    this.name = 'InvalidInteractionError';
    Object.setPrototypeOf(this, InvalidInteractionError.prototype);
  }
}
