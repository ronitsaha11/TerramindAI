import type { Map as MapLibreMap } from 'maplibre-gl';
import type { Feature, FeatureCollection, Geometry } from 'geojson';
import { useLayerStore } from '../stores/useLayerStore';
import { useProjectStore } from '../../../stores/useProjectStore';
import type { DatasetStyle } from '../../../core/styles/style.types';
import { compileDatasetStyle } from './style-expression-compiler';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/** Minimal shape of the dataset list response used for extent fitting. */
interface DatasetSummary {
  id: string;
  extent?: [number, number, number, number];
}

export class MapLibreDatasetRenderer {
  private map: MapLibreMap | null = null;
  private unsubLayerStore: (() => void) | null = null;
  private unsubProjectStore: (() => void) | null = null;
  
  // Track datasets we have already loaded and added to the map
  private loadedDatasets: Set<string> = new Set();

  // Original GeoJSON per dataset, kept so spatial-query highlighting can use
  // exact source geometry instead of tile-clipped queryRenderedFeatures output.
  private datasetGeojson: Map<string, FeatureCollection<Geometry>> = new Map();

  // Attribute-based style per dataset. Compiled to MapLibre expressions so
  // the GPU evaluates rules, rather than styling each feature in JS.
  private datasetStyles: Map<string, DatasetStyle> = new Map();
  
  // Track the current active project to clean up when it changes
  private currentProjectId: string | null = null;

  initialize(map: MapLibreMap) {
    this.map = map;
    
    // Listen for project changes to clean up everything
    this.unsubProjectStore = useProjectStore.subscribe((state, prevState) => {
      if (state.activeProjectId !== prevState.activeProjectId) {
        this.currentProjectId = state.activeProjectId;
        this.cleanupAllDatasets();
      }
    });

    // Initial project ID
    this.currentProjectId = useProjectStore.getState().activeProjectId;

    // Listen for visibility toggles
    this.unsubLayerStore = useLayerStore.subscribe((state, prevState) => {
      const currentVisibleIds = new Set(
        state.layers.filter(l => l.visible).map(l => l.id)
      );
      const prevVisibleIds = new Set(
        prevState.layers.filter(l => l.visible).map(l => l.id)
      );

      // Handle newly visible layers
      for (const id of currentVisibleIds) {
        if (!prevVisibleIds.has(id)) {
          this.showDataset(id);
        }
      }

      // Handle newly hidden layers
      for (const id of prevVisibleIds) {
        if (!currentVisibleIds.has(id)) {
          this.hideDataset(id);
        }
      }
    });
  }

  private async showDataset(datasetId: string) {
    if (!this.map || !this.currentProjectId) return;
    
    // If it's already on the map, just make it visible
    if (this.loadedDatasets.has(datasetId)) {
      this.setLayerVisibility(datasetId, true);
      return;
    }

    try {
      // Fetch GeoJSON from new backend endpoint
      const res = await fetch(`${API_BASE_URL}/projects/${this.currentProjectId}/datasets/${datasetId}/geojson`);
      if (!res.ok) {
        console.error(`Failed to fetch geojson for dataset ${datasetId}`);
        return;
      }
      
      const geojson = (await res.json()) as FeatureCollection<Geometry>;

      // MapLibre discards top-level feature ids that are not numeric, so our
      // UUIDs would never reach queryRenderedFeatures. Mirror the id into
      // properties, where it survives hit-testing intact.
      for (const feature of geojson.features ?? []) {
        if (feature.id != null) {
          feature.properties = { ...(feature.properties ?? {}), __feature_id: String(feature.id) };
        }
      }

      const sourceId = `dataset-source-${datasetId}`;

      // Ensure the map hasn't been destroyed or project changed during the fetch
      if (!this.map || this.currentProjectId !== useProjectStore.getState().activeProjectId) return;

      this.map.addSource(sourceId, {
        type: 'geojson',
        data: geojson,
      });

      // Polygon fill layer
      this.map.addLayer({
        id: `dataset-fill-${datasetId}`,
        type: 'fill',
        source: sourceId,
        filter: ['any', ['==', '$type', 'Polygon']],
        paint: {
          'fill-color': '#3b82f6',
          'fill-opacity': 0.4,
        },
      });

      // Polygon / LineString outline layer
      this.map.addLayer({
        id: `dataset-line-${datasetId}`,
        type: 'line',
        source: sourceId,
        filter: ['any', ['==', '$type', 'Polygon'], ['==', '$type', 'LineString']],
        paint: {
          'line-color': '#ffffff',
          'line-width': 3,
        },
      });

      // Point circle layer
      this.map.addLayer({
        id: `dataset-circle-${datasetId}`,
        type: 'circle',
        source: sourceId,
        filter: ['any', ['==', '$type', 'Point']],
        paint: {
          'circle-radius': 6,
          'circle-color': '#ef4444',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
        },
      });

      this.loadedDatasets.add(datasetId);
      this.datasetGeojson.set(datasetId, geojson);

      // Re-apply any style chosen before this dataset was toggled back on.
      const existingStyle = this.datasetStyles.get(datasetId);
      if (existingStyle) this.applyStyleToLayers(datasetId, existingStyle);

      // Fit bounds if the dataset has an extent
      // Note: useDatasetManager holds the API response, but since we are independent here,
      // we can optionally calculate bounds from the GeoJSON or assume a global store.
      // For simplicity, we can get it from the useDatasetManager cache via queryClient 
      // or we can calculate it manually from the features, but wait - the prompt says: 
      // "Call fitBounds using the dataset's already-computed extent field"
      this.fitToDatasetExtent(datasetId);

    } catch (err) {
      console.error('Error rendering MapLibre dataset:', err);
    }
  }

  private hideDataset(datasetId: string) {
    // We can either set layout-visibility to 'none' or completely remove it.
    // The instructions said "explicitly call map.removeLayer... map.removeSource... on toggle-off"
    if (!this.map) return;
    this.removeDatasetFromMap(datasetId);
  }

  private setLayerVisibility(datasetId: string, visible: boolean) {
    if (!this.map) return;
    const layers = [`dataset-fill-${datasetId}`, `dataset-line-${datasetId}`, `dataset-circle-${datasetId}`];
    layers.forEach(l => {
      if (this.map!.getLayer(l)) {
        this.map!.setLayoutProperty(l, 'visibility', visible ? 'visible' : 'none');
      }
    });
  }

  private removeDatasetFromMap(datasetId: string) {
    if (!this.map) return;
    const layers = [`dataset-fill-${datasetId}`, `dataset-line-${datasetId}`, `dataset-circle-${datasetId}`];
    
    layers.forEach(l => {
      if (this.map!.getLayer(l)) {
        this.map!.removeLayer(l);
      }
    });

    const sourceId = `dataset-source-${datasetId}`;
    if (this.map!.getSource(sourceId)) {
      this.map!.removeSource(sourceId);
    }

    this.loadedDatasets.delete(datasetId);
    this.datasetGeojson.delete(datasetId);
  }

  private cleanupAllDatasets() {
    for (const datasetId of this.loadedDatasets) {
      this.removeDatasetFromMap(datasetId);
    }
    this.loadedDatasets.clear();
    this.datasetGeojson.clear();
  }

  private async fitToDatasetExtent(datasetId: string) {
    // Quick and dirty way to fetch the dataset metadata without complex store dependencies
    if (!this.map || !this.currentProjectId) return;
    try {
      const res = await fetch(`${API_BASE_URL}/projects/${this.currentProjectId}/datasets`);
      if (res.ok) {
        const json = await res.json();
        const ds = (json.data as DatasetSummary[]).find((d) => d.id === datasetId);
        if (ds && ds.extent && ds.extent.length === 4) {
          this.map.fitBounds([
            [ds.extent[0], ds.extent[1]], // [minX, minY]
            [ds.extent[2], ds.extent[3]]  // [maxX, maxY]
          ], { padding: 50, duration: 1000 });
        }
      }
    } catch {
      // Ignore
    }
  }

  // ─── Attribute-based Styling ────────────

  /** Features of a loaded dataset, for deriving categories to style by. */
  getDatasetFeatures(datasetId: string): Feature<Geometry>[] {
    return this.datasetGeojson.get(datasetId)?.features ?? [];
  }

  /**
   * Apply (or clear, with null) an attribute-based style for a dataset.
   * The style is remembered so toggling the dataset off and on keeps it.
   */
  setDatasetStyle(datasetId: string, style: DatasetStyle | null) {
    if (style) {
      this.datasetStyles.set(datasetId, style);
    } else {
      this.datasetStyles.delete(datasetId);
    }
    this.applyStyleToLayers(datasetId, style);
  }

  /**
   * Push compiled paint onto the live layers. Passing null restores the
   * renderer's default paint, which compileDatasetStyle emits for an empty
   * style, so clearing needs no separate code path.
   */
  private applyStyleToLayers(datasetId: string, style: DatasetStyle | null) {
    if (!this.map) return;

    const paint = compileDatasetStyle(
      style ?? { defaultStyle: {}, rules: [] }
    );

    const fill = `dataset-fill-${datasetId}`;
    const line = `dataset-line-${datasetId}`;
    const circle = `dataset-circle-${datasetId}`;

    if (this.map.getLayer(fill)) {
      this.map.setPaintProperty(fill, 'fill-color', paint.fillColor);
      this.map.setPaintProperty(fill, 'fill-opacity', paint.fillOpacity);
    }
    if (this.map.getLayer(line)) {
      this.map.setPaintProperty(line, 'line-color', paint.lineColor);
      this.map.setPaintProperty(line, 'line-width', paint.lineWidth);
    }
    if (this.map.getLayer(circle)) {
      this.map.setPaintProperty(circle, 'circle-color', paint.circleColor);
      this.map.setPaintProperty(circle, 'circle-radius', paint.circleRadius);
    }
  }

  // ─── Nearby Query Result Rendering ────────────

  private static NEARBY_SOURCE = 'nearby-query-source';
  private static NEARBY_FILL = 'nearby-query-fill';
  private static NEARBY_LINE = 'nearby-query-line';
  private static NEARBY_CIRCLE = 'nearby-query-circle';
  private static NEARBY_MARKER_SOURCE = 'nearby-marker-source';
  private static NEARBY_MARKER_LAYER = 'nearby-marker-layer';

  /**
   * Render the results of a nearby spatial query as a highlighted layer
   * that is visually distinct from normal dataset rendering.
   */
  showNearbyResults(geojson: FeatureCollection<Geometry>, queryPoint?: { lon: number; lat: number }) {
    if (!this.map) return;

    // Always clean up any previous query result layers first
    this.clearNearbyResults();

    // Add the result features
    this.map.addSource(MapLibreDatasetRenderer.NEARBY_SOURCE, {
      type: 'geojson',
      data: geojson,
    });

    // Bright yellow fill for polygons
    this.map.addLayer({
      id: MapLibreDatasetRenderer.NEARBY_FILL,
      type: 'fill',
      source: MapLibreDatasetRenderer.NEARBY_SOURCE,
      filter: ['==', '$type', 'Polygon'],
      paint: {
        'fill-color': '#facc15',
        'fill-opacity': 0.35,
      },
    });

    // Bright yellow outline for polygons and lines
    this.map.addLayer({
      id: MapLibreDatasetRenderer.NEARBY_LINE,
      type: 'line',
      source: MapLibreDatasetRenderer.NEARBY_SOURCE,
      filter: ['any', ['==', '$type', 'Polygon'], ['==', '$type', 'LineString']],
      paint: {
        'line-color': '#facc15',
        'line-width': 4,
      },
    });

    // Orange circles for point features
    this.map.addLayer({
      id: MapLibreDatasetRenderer.NEARBY_CIRCLE,
      type: 'circle',
      source: MapLibreDatasetRenderer.NEARBY_SOURCE,
      filter: ['==', '$type', 'Point'],
      paint: {
        'circle-radius': 9,
        'circle-color': '#f97316',
        'circle-stroke-width': 3,
        'circle-stroke-color': '#facc15',
      },
    });

    // Add a marker showing where the user clicked
    if (queryPoint) {
      this.map.addSource(MapLibreDatasetRenderer.NEARBY_MARKER_SOURCE, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [queryPoint.lon, queryPoint.lat] },
          properties: {},
        },
      });

      this.map.addLayer({
        id: MapLibreDatasetRenderer.NEARBY_MARKER_LAYER,
        type: 'circle',
        source: MapLibreDatasetRenderer.NEARBY_MARKER_SOURCE,
        paint: {
          'circle-radius': 7,
          'circle-color': '#ef4444',
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ffffff',
        },
      });
    }
  }

  /**
   * Remove all nearby query result layers and sources from the map.
   */
  clearNearbyResults() {
    if (!this.map) return;

    const layers = [
      MapLibreDatasetRenderer.NEARBY_FILL,
      MapLibreDatasetRenderer.NEARBY_LINE,
      MapLibreDatasetRenderer.NEARBY_CIRCLE,
      MapLibreDatasetRenderer.NEARBY_MARKER_LAYER,
    ];
    for (const layerId of layers) {
      if (this.map.getLayer(layerId)) {
        this.map.removeLayer(layerId);
      }
    }

    const sources = [
      MapLibreDatasetRenderer.NEARBY_SOURCE,
      MapLibreDatasetRenderer.NEARBY_MARKER_SOURCE,
    ];
    for (const sourceId of sources) {
      if (this.map.getSource(sourceId)) {
        this.map.removeSource(sourceId);
      }
    }
  }

  // ─── Contains Query Support ────────────

  private static CONTAINS_SOURCE = 'contains-query-source';
  private static CONTAINS_FILL = 'contains-query-fill';
  private static CONTAINS_LINE = 'contains-query-line';
  private static CONTAINS_CIRCLE = 'contains-query-circle';
  private static CONTAINS_SRC_SOURCE = 'contains-source-polygon-source';
  private static CONTAINS_SRC_FILL = 'contains-source-polygon-fill';
  private static CONTAINS_SRC_LINE = 'contains-source-polygon-line';

  /**
   * Id of the polygon fill layer for a dataset, or null when it is not on the
   * map. Callers use this to scope queryRenderedFeatures hit-testing so that
   * spatial-query result layers are never picked up as click targets.
   */
  getDatasetFillLayerId(datasetId: string): string | null {
    if (!this.map) return null;
    const layerId = `dataset-fill-${datasetId}`;
    return this.map.getLayer(layerId) ? layerId : null;
  }

  /** Look up the original, unclipped feature for a dataset by its UUID. */
  getFeatureById(datasetId: string, featureId: string): Feature<Geometry> | null {
    const geojson = this.datasetGeojson.get(datasetId);
    if (!geojson) return null;
    return (
      geojson.features?.find(
        (f: Feature<Geometry>) =>
          String(f.id) === featureId || f.properties?.__feature_id === featureId
      ) ?? null
    );
  }

  /**
   * Render the results of a contains query. The clicked source polygon is drawn
   * in violet and the features contained inside it in green, keeping both
   * visually distinct from base rendering (blue/red) and nearby results
   * (yellow/orange).
   */
  showContainsResults(geojson: FeatureCollection<Geometry>, sourceFeature?: Feature<Geometry> | null) {
    if (!this.map) return;

    // Always clean up any previous contains result layers first
    this.clearContainsResults();
    this.clearIntersectsResults();

    // The clicked polygon itself, drawn underneath the results
    if (sourceFeature) {
      this.map.addSource(MapLibreDatasetRenderer.CONTAINS_SRC_SOURCE, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [sourceFeature] },
      });

      this.map.addLayer({
        id: MapLibreDatasetRenderer.CONTAINS_SRC_FILL,
        type: 'fill',
        source: MapLibreDatasetRenderer.CONTAINS_SRC_SOURCE,
        filter: ['==', '$type', 'Polygon'],
        paint: {
          'fill-color': '#a855f7',
          'fill-opacity': 0.2,
        },
      });

      this.map.addLayer({
        id: MapLibreDatasetRenderer.CONTAINS_SRC_LINE,
        type: 'line',
        source: MapLibreDatasetRenderer.CONTAINS_SRC_SOURCE,
        filter: ['==', '$type', 'Polygon'],
        paint: {
          'line-color': '#a855f7',
          'line-width': 3,
          'line-dasharray': [2, 1.5],
        },
      });
    }

    // The contained features
    this.map.addSource(MapLibreDatasetRenderer.CONTAINS_SOURCE, {
      type: 'geojson',
      data: geojson,
    });

    this.map.addLayer({
      id: MapLibreDatasetRenderer.CONTAINS_FILL,
      type: 'fill',
      source: MapLibreDatasetRenderer.CONTAINS_SOURCE,
      filter: ['==', '$type', 'Polygon'],
      paint: {
        'fill-color': '#22c55e',
        'fill-opacity': 0.4,
      },
    });

    this.map.addLayer({
      id: MapLibreDatasetRenderer.CONTAINS_LINE,
      type: 'line',
      source: MapLibreDatasetRenderer.CONTAINS_SOURCE,
      filter: ['any', ['==', '$type', 'Polygon'], ['==', '$type', 'LineString']],
      paint: {
        'line-color': '#22c55e',
        'line-width': 4,
      },
    });

    this.map.addLayer({
      id: MapLibreDatasetRenderer.CONTAINS_CIRCLE,
      type: 'circle',
      source: MapLibreDatasetRenderer.CONTAINS_SOURCE,
      filter: ['==', '$type', 'Point'],
      paint: {
        'circle-radius': 10,
        'circle-color': '#22c55e',
        'circle-stroke-width': 3,
        'circle-stroke-color': '#ffffff',
      },
    });
  }

  /** Remove all contains query layers and sources from the map. */
  clearContainsResults() {
    if (!this.map) return;

    const layers = [
      MapLibreDatasetRenderer.CONTAINS_FILL,
      MapLibreDatasetRenderer.CONTAINS_LINE,
      MapLibreDatasetRenderer.CONTAINS_CIRCLE,
      MapLibreDatasetRenderer.CONTAINS_SRC_FILL,
      MapLibreDatasetRenderer.CONTAINS_SRC_LINE,
    ];
    for (const layerId of layers) {
      if (this.map.getLayer(layerId)) {
        this.map.removeLayer(layerId);
      }
    }

    const sources = [
      MapLibreDatasetRenderer.CONTAINS_SOURCE,
      MapLibreDatasetRenderer.CONTAINS_SRC_SOURCE,
    ];
    for (const sourceId of sources) {
      if (this.map.getSource(sourceId)) {
        this.map.removeSource(sourceId);
      }
    }
  }

  // ─── Intersects (cross-dataset) Query Support ────────

  private static INTERSECTS_SOURCE = 'intersects-query-source';
  private static INTERSECTS_FILL = 'intersects-query-fill';
  private static INTERSECTS_LINE = 'intersects-query-line';
  private static INTERSECTS_CIRCLE = 'intersects-query-circle';
  private static INTERSECTS_SRC_SOURCE = 'intersects-source-feature-source';
  private static INTERSECTS_SRC_FILL = 'intersects-source-feature-fill';
  private static INTERSECTS_SRC_LINE = 'intersects-source-feature-line';

  /**
   * Render cross-dataset intersection results. The clicked source feature is
   * drawn in rose and the intersecting features from the target dataset in
   * cyan, keeping this distinct from base rendering (blue/red), nearby
   * (yellow/orange) and contains (violet/green).
   */
  showIntersectsResults(geojson: FeatureCollection<Geometry>, sourceFeature?: Feature<Geometry> | null) {
    if (!this.map) return;

    this.clearIntersectsResults();

    if (sourceFeature) {
      this.map.addSource(MapLibreDatasetRenderer.INTERSECTS_SRC_SOURCE, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [sourceFeature] },
      });

      this.map.addLayer({
        id: MapLibreDatasetRenderer.INTERSECTS_SRC_FILL,
        type: 'fill',
        source: MapLibreDatasetRenderer.INTERSECTS_SRC_SOURCE,
        filter: ['==', '$type', 'Polygon'],
        paint: { 'fill-color': '#f43f5e', 'fill-opacity': 0.15 },
      });

      this.map.addLayer({
        id: MapLibreDatasetRenderer.INTERSECTS_SRC_LINE,
        type: 'line',
        source: MapLibreDatasetRenderer.INTERSECTS_SRC_SOURCE,
        filter: ['==', '$type', 'Polygon'],
        paint: { 'line-color': '#f43f5e', 'line-width': 3, 'line-dasharray': [3, 2] },
      });
    }

    this.map.addSource(MapLibreDatasetRenderer.INTERSECTS_SOURCE, {
      type: 'geojson',
      data: geojson,
    });

    this.map.addLayer({
      id: MapLibreDatasetRenderer.INTERSECTS_FILL,
      type: 'fill',
      source: MapLibreDatasetRenderer.INTERSECTS_SOURCE,
      filter: ['==', '$type', 'Polygon'],
      paint: { 'fill-color': '#06b6d4', 'fill-opacity': 0.45 },
    });

    this.map.addLayer({
      id: MapLibreDatasetRenderer.INTERSECTS_LINE,
      type: 'line',
      source: MapLibreDatasetRenderer.INTERSECTS_SOURCE,
      filter: ['any', ['==', '$type', 'Polygon'], ['==', '$type', 'LineString']],
      paint: { 'line-color': '#06b6d4', 'line-width': 2 },
    });

    this.map.addLayer({
      id: MapLibreDatasetRenderer.INTERSECTS_CIRCLE,
      type: 'circle',
      source: MapLibreDatasetRenderer.INTERSECTS_SOURCE,
      filter: ['==', '$type', 'Point'],
      paint: {
        'circle-radius': 5,
        'circle-color': '#06b6d4',
        'circle-stroke-width': 1.5,
        'circle-stroke-color': '#ffffff',
      },
    });
  }

  /** Remove all intersects query layers and sources from the map. */
  clearIntersectsResults() {
    if (!this.map) return;

    const layers = [
      MapLibreDatasetRenderer.INTERSECTS_FILL,
      MapLibreDatasetRenderer.INTERSECTS_LINE,
      MapLibreDatasetRenderer.INTERSECTS_CIRCLE,
      MapLibreDatasetRenderer.INTERSECTS_SRC_FILL,
      MapLibreDatasetRenderer.INTERSECTS_SRC_LINE,
    ];
    for (const layerId of layers) {
      if (this.map.getLayer(layerId)) this.map.removeLayer(layerId);
    }

    const sources = [
      MapLibreDatasetRenderer.INTERSECTS_SOURCE,
      MapLibreDatasetRenderer.INTERSECTS_SRC_SOURCE,
    ];
    for (const sourceId of sources) {
      if (this.map.getSource(sourceId)) this.map.removeSource(sourceId);
    }
  }

  // ─── Natural-Language Query Result Rendering ────────────

  private static NLQ_SOURCE = 'nlq-result-source';
  private static NLQ_FILL = 'nlq-result-fill';
  private static NLQ_LINE = 'nlq-result-line';
  private static NLQ_CIRCLE = 'nlq-result-circle';
  private static NLQ_FOCUS_SOURCE = 'nlq-focus-source';
  private static NLQ_FOCUS_LAYER = 'nlq-focus-layer';

  /**
   * Render the results of a natural-language spatial query.
   *
   * Uses emerald (#10b981) to stay visually distinct from base rendering
   * (blue/red), nearby (yellow/orange), contains (violet/green), and
   * intersects (rose/cyan).
   */
  showNaturalQueryResults(
    geojson: FeatureCollection<Geometry>,
    focus?: { lon: number; lat: number },
  ) {
    if (!this.map) return;

    // Clear any previous NLQ and other spatial-query results.
    this.clearNaturalQueryResults();
    this.clearNearbyResults();
    this.clearContainsResults();
    this.clearIntersectsResults();

    this.map.addSource(MapLibreDatasetRenderer.NLQ_SOURCE, {
      type: 'geojson',
      data: geojson,
    });

    this.map.addLayer({
      id: MapLibreDatasetRenderer.NLQ_FILL,
      type: 'fill',
      source: MapLibreDatasetRenderer.NLQ_SOURCE,
      filter: ['==', '$type', 'Polygon'],
      paint: {
        'fill-color': '#10b981',
        'fill-opacity': 0.35,
      },
    });

    this.map.addLayer({
      id: MapLibreDatasetRenderer.NLQ_LINE,
      type: 'line',
      source: MapLibreDatasetRenderer.NLQ_SOURCE,
      filter: ['any', ['==', '$type', 'Polygon'], ['==', '$type', 'LineString']],
      paint: {
        'line-color': '#10b981',
        'line-width': 3,
      },
    });

    this.map.addLayer({
      id: MapLibreDatasetRenderer.NLQ_CIRCLE,
      type: 'circle',
      source: MapLibreDatasetRenderer.NLQ_SOURCE,
      filter: ['==', '$type', 'Point'],
      paint: {
        'circle-radius': 8,
        'circle-color': '#10b981',
        'circle-stroke-width': 2.5,
        'circle-stroke-color': '#ffffff',
      },
    });

    // A marker showing the focus point (the resolved reference place).
    if (focus) {
      this.map.addSource(MapLibreDatasetRenderer.NLQ_FOCUS_SOURCE, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [focus.lon, focus.lat] },
          properties: {},
        },
      });

      this.map.addLayer({
        id: MapLibreDatasetRenderer.NLQ_FOCUS_LAYER,
        type: 'circle',
        source: MapLibreDatasetRenderer.NLQ_FOCUS_SOURCE,
        paint: {
          'circle-radius': 7,
          'circle-color': '#ef4444',
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ffffff',
        },
      });
    }
  }

  /** Remove all natural-language query result layers and sources. */
  clearNaturalQueryResults() {
    if (!this.map) return;

    const layers = [
      MapLibreDatasetRenderer.NLQ_FILL,
      MapLibreDatasetRenderer.NLQ_LINE,
      MapLibreDatasetRenderer.NLQ_CIRCLE,
      MapLibreDatasetRenderer.NLQ_FOCUS_LAYER,
    ];
    for (const layerId of layers) {
      if (this.map.getLayer(layerId)) this.map.removeLayer(layerId);
    }

    const sources = [
      MapLibreDatasetRenderer.NLQ_SOURCE,
      MapLibreDatasetRenderer.NLQ_FOCUS_SOURCE,
    ];
    for (const sourceId of sources) {
      if (this.map.getSource(sourceId)) this.map.removeSource(sourceId);
    }
  }

  destroy() {
    this.cleanupAllDatasets();
    this.clearNearbyResults();
    this.clearContainsResults();
    this.clearIntersectsResults();
    this.clearNaturalQueryResults();
    if (this.unsubLayerStore) this.unsubLayerStore();
    if (this.unsubProjectStore) this.unsubProjectStore();
    this.map = null;
  }
}
