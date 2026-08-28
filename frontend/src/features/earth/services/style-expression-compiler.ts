import type {
  DataDrivenPropertyValueSpecification,
  ExpressionSpecification,
} from 'maplibre-gl';
import type { Color, DatasetStyle, FeatureStyle, StyleRule } from '../../../core/styles/style.types';

/**
 * Compiles a DatasetStyle into MapLibre paint expressions.
 *
 * The StyleEvaluator in core/styles evaluates the same rules per feature in
 * JavaScript, which is the right shape for the deck.gl path. MapLibre can
 * evaluate the equivalent logic itself on the GPU, so the rules are translated
 * into `case` expressions once and handed to the layer, rather than the CPU
 * touching every feature on every change.
 *
 * Rule order is preserved: `case` picks the first matching branch, which is the
 * same first-match-wins semantics StyleEvaluator implements.
 */

/** RGBA components are 0-255; MapLibre wants a CSS colour string. */
export function colorToCss(color: Color): string {
  const [r, g, b, a] = color;
  return `rgba(${r}, ${g}, ${b}, ${(a / 255).toFixed(3)})`;
}

/** Translate a single rule's condition into a MapLibre boolean expression. */
function compileCondition(rule: StyleRule): ExpressionSpecification | null {
  const prop = rule.property;
  const value = rule.value;

  switch (rule.operator) {
    case 'has':
      return ['has', prop];

    case '==':
    case '!=':
      // Compared as strings so 'geojson' vs numeric-looking ids behave
      // predictably regardless of how the source typed the property.
      return [rule.operator, ['to-string', ['get', prop]], String(value)];

    case '>':
    case '>=':
    case '<':
    case '<=':
      if (typeof value !== 'number') return null;
      return [rule.operator, ['to-number', ['get', prop]], value];

    case 'in': {
      if (!Array.isArray(value)) return null;
      const members = value.map((v) => String(v));
      return ['in', ['to-string', ['get', prop]], ['literal', members]];
    }

    default:
      return null;
  }
}

/**
 * Build a `case` expression for one paint property.
 *
 * Rules that do not set the property are skipped rather than emitting a branch,
 * so a rule that only changes `radius` does not also flatten `fillColor`.
 * Returns the plain fallback when no rule contributes, keeping the common case
 * a constant rather than a needless expression.
 */
function compilePaint<TIn, TOut extends string | number>(
  style: DatasetStyle,
  pick: (featureStyle: FeatureStyle) => TIn | undefined,
  encode: (value: TIn) => TOut,
  fallback: TOut
): DataDrivenPropertyValueSpecification<TOut> {
  const branches: (ExpressionSpecification | TOut)[] = [];

  for (const rule of style.rules ?? []) {
    const picked = pick(rule.style);
    if (picked === undefined) continue;

    const condition = compileCondition(rule);
    if (!condition) continue;

    branches.push(condition, encode(picked));
  }

  const base = pick(style.defaultStyle);
  const defaultValue = base === undefined ? fallback : encode(base);

  if (branches.length === 0) return defaultValue;

  // The style spec's types cannot express a heterogeneous `case` list, so the
  // assembled expression is asserted once here rather than at each call site.
  return ['case', ...branches, defaultValue] as unknown as DataDrivenPropertyValueSpecification<TOut>;
}

export interface CompiledDatasetPaint {
  fillColor: DataDrivenPropertyValueSpecification<string>;
  fillOpacity: DataDrivenPropertyValueSpecification<number>;
  lineColor: DataDrivenPropertyValueSpecification<string>;
  lineWidth: DataDrivenPropertyValueSpecification<number>;
  circleColor: DataDrivenPropertyValueSpecification<string>;
  circleRadius: DataDrivenPropertyValueSpecification<number>;
}

/** Fallbacks match the renderer's original hardcoded paint. */
const DEFAULTS = {
  fillColor: '#3b82f6',
  fillOpacity: 0.4,
  lineColor: '#ffffff',
  lineWidth: 3,
  circleColor: '#ef4444',
  circleRadius: 6,
} as const;

export function compileDatasetStyle(style: DatasetStyle): CompiledDatasetPaint {
  return {
    fillColor: compilePaint(style, (s) => s.fillColor, colorToCss, DEFAULTS.fillColor),
    fillOpacity: compilePaint(style, (s) => s.opacity, (v) => v, DEFAULTS.fillOpacity),
    lineColor: compilePaint(style, (s) => s.lineColor, colorToCss, DEFAULTS.lineColor),
    lineWidth: compilePaint(style, (s) => s.lineWidth, (v) => v, DEFAULTS.lineWidth),
    // Points reuse fillColor so a categorical style colours polygons and points
    // consistently without the caller having to set both.
    circleColor: compilePaint(style, (s) => s.fillColor, colorToCss, DEFAULTS.circleColor),
    circleRadius: compilePaint(style, (s) => s.radius, (v) => v, DEFAULTS.circleRadius),
  };
}
