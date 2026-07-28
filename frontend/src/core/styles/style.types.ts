/**
 * Represents an RGBA color, where each component is 0-255.
 */
export type Color = readonly [number, number, number, number];

/**
 * The supported style operators for evaluating rules against feature properties.
 */
export type StyleOperator = 
  | '=='
  | '!='
  | '>'
  | '>='
  | '<'
  | '<='
  | 'in'
  | 'has';

/**
 * The computed visual style for a specific feature.
 * Used as the final output of the style evaluator.
 */
export interface FeatureStyle {
  readonly fillColor?: Color;
  readonly lineColor?: Color;
  readonly lineWidth?: number;
  readonly radius?: number;
  readonly opacity?: number;
  readonly visible?: boolean;
}

/**
 * A discrete styling rule that applies a FeatureStyle when its condition evaluates to true.
 */
export interface StyleRule {
  readonly property: string;
  readonly operator: StyleOperator;
  readonly value?: unknown;
  readonly style: FeatureStyle;
}

/**
 * The comprehensive styling configuration for a dataset.
 */
export interface DatasetStyle {
  /** The fallback style applied to all features. */
  readonly defaultStyle: FeatureStyle;
  
  /** 
   * A list of rules evaluated sequentially. 
   * The first rule to evaluate to true will be merged with the default style and returned.
   */
  readonly rules?: readonly StyleRule[];
}
