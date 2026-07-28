import type { Map as MapLibreMap } from 'maplibre-gl';
import type { ISpatialQueryEngine } from '../../../core/spatial/spatial-query.interface';
import type { IDatasetRegistry } from '../../../core/datasets/registry/dataset-registry.interface';
import type { BoundingBox } from '../../../core/spatial/spatial.types';
import type { IFeature } from '../../../core/interactions/interaction.types';
import type { ViewportQueryListener, ViewportQueryResult, VisibleDatasetResult } from '../types/viewport-query.types';

export class ViewportQueryController {
  private readonly spatialEngine: ISpatialQueryEngine;
  private readonly registry: IDatasetRegistry;
  private readonly listeners: Set<ViewportQueryListener> = new Set();
  
  private debounceTimer: number | null = null;
  private readonly debounceMs = 250;

  constructor(spatialEngine: ISpatialQueryEngine, registry: IDatasetRegistry) {
    this.spatialEngine = spatialEngine;
    this.registry = registry;
  }

  /**
   * Subscribes a listener to viewport query updates.
   */
  public subscribe(listener: ViewportQueryListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Binds the controller to map events.
   */
  public bind(map: MapLibreMap): void {
    // Listen to moveend instead of every frame during movement.
    // We still debounce it just in case of rapid programmatic camera jumps.
    map.on('moveend', () => this.handleViewportChange(map));
    
    // Also perform an initial query
    this.handleViewportChange(map);
  }

  /**
   * Debounces viewport updates and executes the query.
   */
  private handleViewportChange(map: MapLibreMap): void {
    if (this.debounceTimer !== null) {
      window.clearTimeout(this.debounceTimer);
    }

    this.debounceTimer = window.setTimeout(() => {
      this.debounceTimer = null;
      this.executeQuery(map);
    }, this.debounceMs);
  }

  /**
   * Executes the spatial query against all registered datasets.
   */
  private executeQuery(map: MapLibreMap): void {
    const bounds = map.getBounds();
    
    // MapLibre bounds: West, South, East, North (minLng, minLat, maxLng, maxLat)
    const bbox: BoundingBox = [
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth()
    ];

    const datasets = this.registry.list();
    const datasetResults: VisibleDatasetResult[] = [];
    
    let totalFeatures = 0;
    let totalMs = 0;

    for (const dataset of datasets) {
      // Create a temporary array of IFeature to pass to the spatial engine.
      // We assume dataset.data.features is an array of GeoJSON features.
      // In a real scenario, the dataset domain object would expose IFeature[].
      // For now, we map them purely for the engine.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const rawData = dataset.data as any;
      const rawFeatures = Array.isArray(rawData?.features) ? rawData.features : [];
      
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const domainFeatures: IFeature[] = rawFeatures.map((raw: any) => ({
        id: raw.id ?? raw.properties?.id ?? '',
        datasetId: dataset.id,
        properties: raw.properties || {},
        geometry: raw.geometry
      }));

      // Only query if there are features
      if (domainFeatures.length > 0) {
        const result = this.spatialEngine.findInBoundingBox(domainFeatures, bbox);
        
        datasetResults.push(Object.freeze({
          datasetId: dataset.id,
          visibleFeatures: result.features,
          featureCount: result.count,
          elapsedMs: result.elapsedMs
        }));

        totalFeatures += result.count;
        totalMs += result.elapsedMs;
      }
    }

    const finalResult: ViewportQueryResult = Object.freeze({
      datasets: Object.freeze(datasetResults),
      totalVisibleFeatures: totalFeatures,
      totalElapsedMs: totalMs,
      timestamp: Date.now()
    });

    this.notifyListeners(finalResult);
  }

  private notifyListeners(result: ViewportQueryResult): void {
    for (const listener of this.listeners) {
      try {
        listener(result);
      } catch (err) {
        console.error('ViewportQueryController: Error in listener', err);
      }
    }
  }
}
