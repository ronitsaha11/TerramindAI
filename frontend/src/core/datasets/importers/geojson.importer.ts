import type { IDatasetImporter } from '../contracts/importer.interface';
import type { IDatasetValidator } from '../contracts/validator.interface';
import type { IMetadataProvider } from '../contracts/metadata-provider.interface';
import type { IDataset } from '../models/dataset';
import type { IDatasetMetadata } from '../metadata/metadata.interface';
import { ValidationError } from '../errors/dataset.error';

/**
 * Orchestrates the GeoJSON import pipeline.
 * Responsibility: Coordinates validation, metadata generation, and construction of an immutable IDataset.
 * Ownership: Manages the import workflow but does not register the dataset or perform domain logic itself.
 */
export class GeoJsonImporter implements IDatasetImporter<unknown, unknown> {
  private readonly validator: IDatasetValidator<unknown>;
  private readonly metadataProvider: IMetadataProvider<unknown, IDatasetMetadata>;

  /**
   * Initializes a new instance of the GeoJsonImporter.
   * 
   * @param validator - The validator to check GeoJSON structure.
   * @param metadataProvider - The provider to compute GeoJSON metadata.
   */
  constructor(
    validator: IDatasetValidator<unknown>,
    metadataProvider: IMetadataProvider<unknown, IDatasetMetadata>
  ) {
    this.validator = validator;
    this.metadataProvider = metadataProvider;
  }

  public async import(input: unknown, name: string): Promise<IDataset<unknown>> {
    // 1. Validate
    const validationResult = await this.validator.validate(input);
    if (!validationResult.isValid) {
      const errorMessages = validationResult.issues
        .filter(issue => issue.severity === 'error')
        .map(issue => issue.message)
        .join('; ');
      
      throw new ValidationError(`GeoJSON validation failed: ${errorMessages}`);
    }

    // 2. Compute Metadata
    const metadata = await this.metadataProvider.compute(input);

    // 3. Construct immutable dataset
    const dataset: IDataset<unknown> = {
      id: crypto.randomUUID(),
      name,
      type: 'geojson',
      state: 'ready',
      data: input,
      metadata,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    // 4. Return dataset
    return dataset;
  }
}
