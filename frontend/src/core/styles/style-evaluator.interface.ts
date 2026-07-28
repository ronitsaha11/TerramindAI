import type { IFeature } from '../interactions/interaction.types';
import type { DatasetStyle, FeatureStyle } from './style.types';

/**
 * Core domain service responsible for evaluating a DatasetStyle against a given feature.
 * 
 * It is completely pure, contains no side-effects, and knows nothing about
 * rendering engines like Deck.gl, MapLibre, or React.
 */
export interface IStyleEvaluator {
  /**
   * Evaluates the dataset style rules against the given feature properties
   * to produce a finalized FeatureStyle.
   * 
   * @param feature - The domain feature (provides properties for rule evaluation).
   * @param datasetStyle - The JSON-serializable dataset style configuration.
   * @returns The resolved immutable FeatureStyle for this specific feature.
   */
  evaluate(feature: IFeature, datasetStyle: DatasetStyle): FeatureStyle;
}
