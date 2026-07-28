import type { IDataset } from '../models/dataset';
import type { DatasetLayerDefinition } from './dataset-layer-definition.ts';
import type { IDatasetLayerFactory } from './dataset-layer.factory.interface';
import { UnsupportedDatasetTypeError } from './rendering.error';
import type { IStyleEvaluator } from '../../styles/style-evaluator.interface';
import type { DatasetStyle, FeatureStyle } from '../../styles/style.types';
import type { IFeature } from '../../interactions/interaction.types';

/**
 * Implementation of IDatasetLayerFactory.
 * Translates Datasets into renderer-agnostic layer definitions.
 */
export class DatasetLayerFactory implements IDatasetLayerFactory {
  private readonly styleEvaluator: IStyleEvaluator;

  constructor(styleEvaluator: IStyleEvaluator) {
    this.styleEvaluator = styleEvaluator;
  }

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
          getFillColor: (d: unknown) => this.evaluateFeature(d, dataset).fillColor ?? [100, 150, 250, 150],
          getLineColor: (d: unknown) => this.evaluateFeature(d, dataset).lineColor ?? [200, 200, 200, 255],
          getLineWidth: (d: unknown) => this.evaluateFeature(d, dataset).lineWidth ?? 2,
          getRadius: (d: unknown) => this.evaluateFeature(d, dataset).radius ?? 5,
        }),
        metadata: Object.freeze({ ...dataset.metadata }),
      };
    }

    throw new UnsupportedDatasetTypeError(
      `Cannot create layer definition for unsupported dataset type: ${dataset.type}`
    );
  }

  private getDefaultStyle(): DatasetStyle {
    return {
      defaultStyle: {
        fillColor: [100, 150, 250, 150],
        lineColor: [200, 200, 200, 255],
        lineWidth: 2,
        radius: 5,
      },
    };
  }

  private evaluateFeature(rawFeature: unknown, dataset: IDataset): FeatureStyle {
    const feature = this.mapToIFeature(rawFeature, dataset.id);
    const styleDef = dataset.style ?? this.getDefaultStyle();
    return this.styleEvaluator.evaluate(feature, styleDef);
  }

  private mapToIFeature(rawFeature: unknown, datasetId: string): IFeature {
    const raw = rawFeature as Record<string, unknown>;
    const properties = (raw.properties as Record<string, unknown>) || {};
    
    return {
      id: (typeof raw.id === 'string' ? raw.id : undefined) ?? 
          (typeof properties.id === 'string' ? properties.id : undefined) ?? 
          '',
      datasetId,
      properties,
      geometry: raw.geometry,
    };
  }
}
