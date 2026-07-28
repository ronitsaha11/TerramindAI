import type { IDataset } from '../models/dataset';
import type { DatasetLayerDefinition } from './dataset-layer-definition.ts';
import type { IDatasetLayerFactory } from './dataset-layer.factory.interface';
import { UnsupportedDatasetTypeError } from './rendering.error';

/**
 * Implementation of IDatasetLayerFactory.
 * Translates Datasets into renderer-agnostic layer definitions.
 */
export class DatasetLayerFactory implements IDatasetLayerFactory {
  public create(dataset: IDataset): DatasetLayerDefinition {
    // For Micro-Sprint 11.4.6 we handle geojson. Other types will throw.
    if (dataset.type === 'geojson') {
      return {
        id: `layer-${dataset.id}`,
        datasetId: dataset.id,
        name: dataset.name,
        datasetType: dataset.type,
        renderType: 'geojson',
        visible: true,
        opacity: 1,
        sourceData: dataset.data,
        style: Object.freeze({
          fillColor: [100, 150, 250, 150],
          lineColor: [200, 200, 200, 255],
          lineWidth: 2,
          radius: 5,
        }),
        metadata: Object.freeze({ ...dataset.metadata }),
      };
    }

    throw new UnsupportedDatasetTypeError(
      `Cannot create layer definition for unsupported dataset type: ${dataset.type}`
    );
  }
}
