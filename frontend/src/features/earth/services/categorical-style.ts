import type { Feature, Geometry } from 'geojson';
import type { Color, DatasetStyle, StyleRule } from '../../../core/styles/style.types';

/**
 * Derives a categorical DatasetStyle from the values actually present in a
 * dataset, so styling reflects the real data rather than a guessed schema.
 */

/**
 * Okabe-Ito, which stays distinguishable under the common forms of colour
 * vision deficiency and reads against a dark basemap.
 */
const PALETTE_HEX = [
  '#E69F00', // orange
  '#56B4E9', // sky blue
  '#009E73', // green
  '#F0E442', // yellow
  '#0072B2', // blue
  '#D55E00', // vermillion
  '#CC79A7', // reddish purple
  '#94D0FF', // pale blue
  '#B5EAD7', // mint
  '#FFB3B3', // salmon
  '#C7B3FF', // lavender
  '#9C9C9C', // grey
] as const;

/** Categories beyond the palette keep the dataset's default colour. */
export const MAX_CATEGORIES = PALETTE_HEX.length;

function hexToColor(hex: string, alpha = 255): Color {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255, alpha] as const;
}

export const PALETTE: readonly Color[] = PALETTE_HEX.map((h) => hexToColor(h));

export interface CategorySummary {
  value: string;
  count: number;
  color: Color;
}

/**
 * Properties worth offering as a styling dimension: present on most features
 * and with few enough distinct values to read as categories. Free-text fields
 * like `name` are excluded by the cardinality check rather than by name, so
 * this holds for datasets we have not seen.
 */
export function styleableProperties(features: Feature<Geometry>[]): string[] {
  if (features.length === 0) return [];

  const counts = new Map<string, Map<string, number>>();
  for (const f of features) {
    for (const [k, v] of Object.entries(f.properties ?? {})) {
      if (k === '__feature_id') continue;
      if (v === null || v === undefined || typeof v === 'object') continue;
      let distinct = counts.get(k);
      if (!distinct) {
        distinct = new Map();
        counts.set(k, distinct);
      }
      const s = String(v);
      distinct.set(s, (distinct.get(s) ?? 0) + 1);
    }
  }

  const result: string[] = [];
  for (const [key, distinct] of counts) {
    // At least two categories to be worth colouring, and not so many that the
    // legend becomes noise (ids and names fall out here).
    if (distinct.size < 2) continue;
    if (distinct.size > features.length * 0.5) continue;
    if (distinct.size > 50) continue;
    result.push(key);
  }
  return result.sort();
}

/** Distinct values of a property, most frequent first, with assigned colours. */
export function summariseCategories(
  features: Feature<Geometry>[],
  property: string
): CategorySummary[] {
  const counts = new Map<string, number>();
  for (const f of features) {
    const v = f.properties?.[property];
    if (v === null || v === undefined || typeof v === 'object') continue;
    const s = String(v);
    counts.set(s, (counts.get(s) ?? 0) + 1);
  }

  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, MAX_CATEGORIES)
    .map(([value, count], i) => ({ value, count, color: PALETTE[i] }));
}

/**
 * One equality rule per category. Rule order mirrors the legend, and the first
 * match wins, matching StyleEvaluator's semantics.
 */
export function buildCategoricalStyle(
  property: string,
  categories: CategorySummary[]
): DatasetStyle {
  const rules: StyleRule[] = categories.map((c) => ({
    property,
    operator: '==' as const,
    value: c.value,
    style: { fillColor: c.color, lineColor: c.color },
  }));

  return {
    // Uncategorised features stay visible but muted, so gaps in the data are
    // obvious instead of silently vanishing.
    defaultStyle: {
      fillColor: [120, 120, 120, 255],
      lineColor: [160, 160, 160, 255],
      opacity: 0.35,
    },
    rules,
  };
}
