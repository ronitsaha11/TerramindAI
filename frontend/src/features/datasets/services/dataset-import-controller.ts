import { DatasetManager } from '../../../core/datasets/services/dataset-manager';
import { GeoJsonImporter } from '../../../core/datasets/importers/geojson.importer';
import { GeoJsonValidator } from '../../../core/datasets/validation/geojson.validator';
import { GeoJsonMetadataProvider } from '../../../core/datasets/metadata/geojson-metadata-provider';
import type { IDatasetRegistry } from '../../../core/datasets/registry/dataset-registry.interface';
import { ValidationError } from '../../../core/datasets/errors/dataset.error';

export interface ImportResult {
  readonly success: boolean;
  readonly datasetId?: string;
  readonly error?: string;
}

export class DatasetImportController {
  private readonly manager: DatasetManager;
  private readonly registry: IDatasetRegistry;

  constructor(registry: IDatasetRegistry) {
    this.registry = registry;
    this.manager = new DatasetManager(registry);
  }

  public async importFile(file: File): Promise<ImportResult> {
    try {
      // 1. Basic validation
      if (!file.name.endsWith('.json') && !file.name.endsWith('.geojson')) {
        return { success: false, error: 'Unsupported file extension. Please provide a .geojson or .json file.' };
      }

      // Check for duplicate by name (naive check)
      const isDuplicate = this.registry.list().some(d => d.name === file.name);
      if (isDuplicate) {
        return { success: false, error: 'A dataset with this name is already loaded.' };
      }

      // 2. Read file
      const fileContent = await this.readFileAsText(file);

      // 3. Parse JSON
      let parsedJson: unknown;
      try {
        parsedJson = JSON.parse(fileContent);
      } catch {
        return { success: false, error: 'Invalid JSON format. The file could not be parsed.' };
      }

      // 4. Construct domain pipeline
      const validator = new GeoJsonValidator();
      const metadataProvider = new GeoJsonMetadataProvider();
      const importer = new GeoJsonImporter(validator, metadataProvider);

      // 5. Invoke domain manager
      const dataset = await this.manager.importDataset(importer, parsedJson, file.name);

      return { success: true, datasetId: dataset.id };

    } catch (err) {
      if (err instanceof ValidationError) {
        return { success: false, error: err.message };
      }
      return { success: false, error: 'An unexpected error occurred during import.' };
    }
  }

  private readFileAsText(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (typeof e.target?.result === 'string') {
          resolve(e.target.result);
        } else {
          reject(new Error('Failed to read file as text.'));
        }
      };
      reader.onerror = () => reject(new Error('Error reading file.'));
      reader.readAsText(file);
    });
  }
}
