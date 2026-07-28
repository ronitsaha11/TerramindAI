import type { IValidationResult } from '../validation/validation.types';

/**
 * Responsible for validating input data before or after dataset creation.
 * Ownership: Ensures data integrity and format correctness.
 */
export interface IDatasetValidator<TInput> {
  /**
   * Validates the provided input.
   * 
   * @param input - The input data to validate.
   * @returns A promise resolving to the validation result.
   */
  validate(input: TInput): Promise<IValidationResult>;
}
