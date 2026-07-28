import type { IMetadataProvider } from '../contracts/metadata-provider.interface';
import type { IDatasetMetadata } from './metadata.interface';

/**
 * Computes metadata for GeoJSON structures.
 * Responsibility: Extracts lightweight metadata (like feature count) from raw GeoJSON input.
 * Ownership: Operates purely on input data to derive metadata, without mutating it or validating it.
 */
export class GeoJsonMetadataProvider implements IMetadataProvider<unknown, IDatasetMetadata> {
  public async compute(input: unknown): Promise<IDatasetMetadata> {
    const metadata: IDatasetMetadata = {
      customProps: {}
    };

    if (!input || typeof input !== 'object') {
      return metadata;
    }

    const geojson = input as Record<string, unknown>;

    if (geojson.type === 'FeatureCollection' && Array.isArray(geojson.features)) {
      metadata.featureCount = geojson.features.length;
    } else if (geojson.type === 'Feature') {
      metadata.featureCount = 1;
    }

    // Future bounds and statistics generation would occur here
    // but are intentionally omitted for this micro-sprint.

    return metadata;
  }
}
