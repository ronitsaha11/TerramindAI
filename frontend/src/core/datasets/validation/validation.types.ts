/**
 * Represents the severity of a validation issue.
 */
export type ValidationSeverity = 'info' | 'warning' | 'error';

/**
 * Represents a specific validation issue found within a dataset.
 */
export interface IValidationIssue {
  /**
   * A unique, stable code identifying the type of issue.
   */
  code: string;

  /**
   * A human-readable description of the issue.
   */
  message: string;

  /**
   * The severity of the issue.
   */
  severity: ValidationSeverity;

  /**
   * Optional path to the specific location of the issue within the dataset structure.
   */
  path?: string;
}

/**
 * Represents the result of validating a dataset or dataset input.
 */
export interface IValidationResult {
  /**
   * Indicates whether the validation passed.
   * Typically true if there are no 'error' severity issues.
   */
  isValid: boolean;

  /**
   * A list of issues found during validation.
   */
  issues: IValidationIssue[];
}
