import type { IFeature } from '../interactions/interaction.types';
import type { IStyleEvaluator } from './style-evaluator.interface';
import type { DatasetStyle, FeatureStyle, StyleRule } from './style.types';

export class StyleEvaluator implements IStyleEvaluator {
  public evaluate(feature: IFeature, datasetStyle: DatasetStyle): FeatureStyle {
    const baseStyle = datasetStyle.defaultStyle;

    if (!datasetStyle.rules || datasetStyle.rules.length === 0) {
      return this.mergeStyles(baseStyle, {});
    }

    for (const rule of datasetStyle.rules) {
      if (this.evaluateRule(feature.properties, rule)) {
        return this.mergeStyles(baseStyle, rule.style);
      }
    }

    return this.mergeStyles(baseStyle, {});
  }

  /**
   * Safely merges a matched rule style on top of the base default style.
   */
  private mergeStyles(base: FeatureStyle, overlay: FeatureStyle): FeatureStyle {
    return Object.freeze({
      ...base,
      ...overlay,
    });
  }

  /**
   * Safely evaluates a single rule against a feature's properties.
   * Missing properties evaluate to false safely without throwing errors.
   */
  private evaluateRule(properties: Readonly<Record<string, unknown>>, rule: StyleRule): boolean {
    const featureValue = properties[rule.property];

    try {
      switch (rule.operator) {
        case 'has':
          return rule.property in properties;
        
        case '==':
          return featureValue === rule.value;
          
        case '!=':
          return featureValue !== rule.value;
          
        case '>':
          if (typeof featureValue !== 'number' || typeof rule.value !== 'number') return false;
          return featureValue > rule.value;
          
        case '>=':
          if (typeof featureValue !== 'number' || typeof rule.value !== 'number') return false;
          return featureValue >= rule.value;
          
        case '<':
          if (typeof featureValue !== 'number' || typeof rule.value !== 'number') return false;
          return featureValue < rule.value;
          
        case '<=':
          if (typeof featureValue !== 'number' || typeof rule.value !== 'number') return false;
          return featureValue <= rule.value;
          
        case 'in':
          if (!Array.isArray(rule.value)) return false;
          return rule.value.includes(featureValue);
          
        default:
          return false;
      }
    } catch (e) {
      // In the rare event an evaluation crashes (e.g. proxy getter traps),
      // we log safely and return false to continue to the next rule.
      console.warn(`StyleEvaluator: Failed to evaluate rule for property '${rule.property}'.`, e);
      return false;
    }
  }
}
