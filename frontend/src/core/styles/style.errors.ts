/**
 * Base error for all style evaluation issues.
 */
export class StyleError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'StyleError';
    Object.setPrototypeOf(this, StyleError.prototype);
  }
}

/**
 * Thrown when an error occurs during the evaluation of a style rule.
 */
export class StyleEvaluationError extends StyleError {
  constructor(message: string) {
    super(message);
    this.name = 'StyleEvaluationError';
    Object.setPrototypeOf(this, StyleEvaluationError.prototype);
  }
}

/**
 * Thrown when an invalid style rule configuration is provided.
 */
export class InvalidStyleRuleError extends StyleError {
  constructor(message: string) {
    super(message);
    this.name = 'InvalidStyleRuleError';
    Object.setPrototypeOf(this, InvalidStyleRuleError.prototype);
  }
}
