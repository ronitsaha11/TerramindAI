/**
 * Responsible for computing or extracting metadata for a given input or dataset.
 * Ownership: Analyzes data to derive descriptive information like bounds or feature counts.
 */
export interface IMetadataProvider<TInput, TMetadata> {
  /**
   * Computes metadata for the given input.
   * 
   * @param input - The input data from which to compute metadata.
   * @returns A promise resolving to the computed metadata.
   */
  compute(input: TInput): Promise<TMetadata>;
}
