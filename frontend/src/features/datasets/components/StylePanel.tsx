import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Palette, X } from 'lucide-react';
import type { Feature, Geometry } from 'geojson';
import { Button } from '@/components/ui/button';
import { useDatasetStyleStore } from '../../earth/stores/useDatasetStyleStore';
import { useLayerStore } from '../../earth/stores/useLayerStore';
import { EarthEngine } from '../../earth/services/EarthEngine';
import {
  buildCategoricalStyle,
  summariseCategories,
  styleableProperties,
  MAX_CATEGORIES,
} from '../../earth/services/categorical-style';
import { colorToCss } from '../../earth/services/style-expression-compiler';

const EMPTY: Feature<Geometry>[] = [];

export function StylePanel() {
  const styleProperty = useDatasetStyleStore((s) => s.styleProperty);
  const setStyleProperty = useDatasetStyleStore((s) => s.setStyleProperty);
  const clearDataset = useDatasetStyleStore((s) => s.clearDataset);

  const visibleDatasetId = useLayerStore((s) => {
    const visible = s.layers.find((l) => l.visible && l.category === 'geojson');
    return visible?.id ?? null;
  });

  // Keyed by dataset so switching datasets does not require clearing state
  // synchronously inside the effect, which would cascade renders.
  const [loaded, setLoaded] = useState<{
    datasetId: string;
    features: Feature<Geometry>[];
  } | null>(null);
  const retryRef = useRef<number | null>(null);

  // Memoised so the empty-array branch does not produce a new reference on
  // every render, which would re-run the re-apply effect continuously.
  const features = useMemo(
    () => (loaded && loaded.datasetId === visibleDatasetId ? loaded.features : EMPTY),
    [loaded, visibleDatasetId]
  );

  // A dataset's GeoJSON arrives asynchronously after it is toggled on, so poll
  // briefly for it rather than reading once and showing an empty panel.
  useEffect(() => {
    if (!visibleDatasetId) return;

    let attempts = 0;
    const tick = () => {
      attempts += 1;
      const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
      const f = renderer?.getDatasetFeatures(visibleDatasetId) ?? [];
      if (f.length > 0 || attempts > 30) {
        if (retryRef.current) window.clearInterval(retryRef.current);
        retryRef.current = null;
        if (f.length > 0) setLoaded({ datasetId: visibleDatasetId, features: f });
      }
    };

    retryRef.current = window.setInterval(tick, 300);

    return () => {
      if (retryRef.current) window.clearInterval(retryRef.current);
      retryRef.current = null;
    };
  }, [visibleDatasetId]);

  const properties = useMemo(() => styleableProperties(features), [features]);
  const active = visibleDatasetId ? (styleProperty[visibleDatasetId] ?? null) : null;

  const categories = useMemo(
    () => (active ? summariseCategories(features, active) : []),
    [features, active]
  );

  const apply = useCallback(
    (property: string | null) => {
      if (!visibleDatasetId) return;
      const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();

      if (!property) {
        renderer?.setDatasetStyle(visibleDatasetId, null);
        clearDataset(visibleDatasetId);
        return;
      }

      const cats = summariseCategories(features, property);
      renderer?.setDatasetStyle(visibleDatasetId, buildCategoricalStyle(property, cats));
      setStyleProperty(visibleDatasetId, property);
    },
    [visibleDatasetId, features, setStyleProperty, clearDataset]
  );

  // Re-apply on remount or dataset re-toggle so the legend and the map agree.
  useEffect(() => {
    if (!visibleDatasetId || !active || features.length === 0) return;
    const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
    const cats = summariseCategories(features, active);
    renderer?.setDatasetStyle(visibleDatasetId, buildCategoricalStyle(active, cats));
  }, [visibleDatasetId, active, features]);

  if (!visibleDatasetId) return null;

  const distinctTotal = active
    ? new Set(features.map((f) => String(f.properties?.[active]))).size
    : 0;

  return (
    <div className="border-t pt-3 mt-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase text-muted-foreground tracking-tight">
          Styling
        </span>
        {active && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs gap-1 text-muted-foreground hover:text-zinc-200"
            onClick={() => apply(null)}
            aria-label="Clear attribute styling"
          >
            <X className="w-3 h-3" />
            Reset
          </Button>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Palette className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
        <label className="text-xs text-muted-foreground whitespace-nowrap">Colour by:</label>
        <select
          value={active ?? ''}
          onChange={(e) => apply(e.target.value || null)}
          disabled={properties.length === 0}
          className="flex-1 h-7 px-2 text-xs rounded-md bg-zinc-800 border border-zinc-700 text-zinc-200 focus:outline-none focus:border-zinc-500 disabled:opacity-50"
          aria-label="Attribute to colour features by"
        >
          <option value="">None</option>
          {properties.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      {features.length === 0 && (
        <p className="text-xs text-muted-foreground">
          Toggle a dataset on to style it.
        </p>
      )}

      {features.length > 0 && properties.length === 0 && (
        <p className="text-xs text-muted-foreground">
          No attribute in this dataset has usable categories.
        </p>
      )}

      {categories.length > 0 && (
        <div className="space-y-1">
          {categories.map((c) => (
            <div key={c.value} className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-sm shrink-0 border border-black/40"
                style={{ backgroundColor: colorToCss(c.color) }}
              />
              <span className="text-xs text-zinc-300 truncate flex-1" title={c.value}>
                {c.value}
              </span>
              <span className="text-xs text-muted-foreground tabular-nums">
                {c.count.toLocaleString()}
              </span>
            </div>
          ))}
          {distinctTotal > MAX_CATEGORIES && (
            <p className="text-xs text-muted-foreground pt-1">
              Showing top {MAX_CATEGORIES} of {distinctTotal.toLocaleString()}; the rest stay grey.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
