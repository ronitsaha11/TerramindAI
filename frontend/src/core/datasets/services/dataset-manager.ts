import type { IDatasetManager } from './dataset-manager.interface';
import type { IDatasetRegistry } from '../registry/dataset-registry.interface';
import type { IDatasetImporter } from '../contracts/importer.interface';
import type { IDataset } from '../models/dataset';

/**
 * Implementation of the Dataset Manager Service.
 * Coordinates workflows between Importers and the Dataset Registry.
 * Dependencies are injected; it does not instantiate its own dependencies.
 */
export class DatasetManager implements IDatasetManager {
  private readonly registry: IDatasetRegistry;

  /**
   * Initializes a new instance of the DatasetManager.
   * 
   * @param registry - The authoritative registry serving as the single source of truth for datasets.
   */
  constructor(registry: IDatasetRegistry) {
    this.registry = registry;
  }

  public async importDataset<TInput>(
    importer: IDatasetImporter<TInput, unknown>,
    input: TInput,
    name: string
  ): Promise<IDataset> {
    // 1. Delegate actual processing to the specialized importer.
    // The importer validates, computes metadata, and constructs the immutable Dataset.
    const dataset = await importer.import(input, name);

    // 2. Register the newly created dataset into the single source of truth.
    this.registry.register(dataset);

    // 3. Return the fully formed and registered dataset.
    return dataset;
  }

  public removeDataset(id: string): void {
    this.registry.unregister(id);
  }

  public getDataset(id: string): IDataset | undefined {
    return this.registry.get(id);
  }

  public listDatasets(): ReadonlyArray<IDataset> {
    return this.registry.list();
  }

  public countDatasets(): number {
    return this.registry.count();
  }

  public hasDataset(id: string): boolean {
    return this.registry.has(id);
  }

  public clearDatasets(): void {
    this.registry.clear();
  }
}
