import { useCallback, useEffect, useRef } from 'react';
import { Layers, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useIntersectsQueryStore } from '../../earth/stores/useIntersectsQueryStore';
import { useContainsQueryStore } from '../../earth/stores/useContainsQueryStore';
import { useNearbyQueryStore } from '../../earth/stores/useNearbyQueryStore';
import { useLayerStore } from '../../earth/stores/useLayerStore';
import { useProjectStore } from '../../../stores/useProjectStore';
import { useDatasetManager } from '../hooks/useDatasetManager';
import { EarthEngine } from '../../earth/services/EarthEngine';
import { NotificationService } from '../../../shared/services/notification.service';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export function IntersectsQueryPanel() {
  const active = useIntersectsQueryStore((s) => s.active);
  const targetDatasetId = useIntersectsQueryStore((s) => s.targetDatasetId);
  const sourceFeature = useIntersectsQueryStore((s) => s.sourceFeature);
  const results = useIntersectsQueryStore((s) => s.results);
  const loading = useIntersectsQueryStore((s) => s.loading);

  const activate = useIntersectsQueryStore((s) => s.activate);
  const deactivate = useIntersectsQueryStore((s) => s.deactivate);
  const setTargetDatasetId = useIntersectsQueryStore((s) => s.setTargetDatasetId);
  const setSourceFeature = useIntersectsQueryStore((s) => s.setSourceFeature);
  const setResults = useIntersectsQueryStore((s) => s.setResults);
  const setLoading = useIntersectsQueryStore((s) => s.setLoading);
  const clear = useIntersectsQueryStore((s) => s.clear);

  // Every query mode owns a capture-phase canvas click handler, so only one
  // may be active at a time.
  const nearbyActive = useNearbyQueryStore((s) => s.active);
  const containsActive = useContainsQueryStore((s) => s.active);

  const clickHandlerRef = useRef<((e: MouseEvent) => void) | null>(null);

  const { datasets } = useDatasetManager();
  const projectId = useProjectStore((s) => s.activeProjectId);

  const visibleDatasetId = useLayerStore((s) => {
    const visible = s.layers.find((l) => l.visible && l.category === 'geojson');
    return visible?.id ?? null;
  });

  // Default the target to the first dataset that is not the one being clicked.
  useEffect(() => {
    if (targetDatasetId) return;
    const candidate = datasets.find((d) => d.id !== visibleDatasetId);
    if (candidate) setTargetDatasetId(candidate.id);
  }, [datasets, visibleDatasetId, targetDatasetId, setTargetDatasetId]);

  const executeQuery = useCallback(
    async (featureId: string, featureName: string) => {
      if (!projectId || !visibleDatasetId) {
        NotificationService.error('No visible dataset to query. Toggle a dataset on first.');
        return;
      }
      if (!targetDatasetId) {
        NotificationService.error('Pick a target dataset to intersect against.');
        return;
      }

      setLoading(true);

      try {
        const url =
          `${API_BASE_URL}/projects/${projectId}/datasets/${visibleDatasetId}` +
          `/query/intersects?feature_id=${featureId}&target_dataset_id=${targetDatasetId}`;
        const res = await fetch(url);

        if (!res.ok) {
          const errText = await res.text();
          throw new Error(errText);
        }

        const geojson = await res.json();
        setResults(geojson);

        const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
        const source = renderer?.getFeatureById(visibleDatasetId, featureId);
        renderer?.showIntersectsResults(geojson, source);

        const count = geojson.features?.length ?? 0;
        NotificationService.success(
          `${count} feature${count !== 1 ? 's' : ''} intersecting ${featureName}`
        );
      } catch (err) {
        console.error('Intersects query failed:', err);
        NotificationService.error('Intersects query failed. Check console for details.');
        setResults(null);
      }
    },
    [projectId, visibleDatasetId, targetDatasetId, setResults, setLoading]
  );

  // Register / unregister the map click handler when mode is toggled
  useEffect(() => {
    const map = EarthEngine.getInstance().getMap();
    if (!map) {
      console.warn('[IntersectsQueryPanel] Map is not available yet.');
      return;
    }

    if (active) {
      map.getCanvas().style.cursor = 'crosshair';

      const handler = (e: MouseEvent) => {
        const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
        const fillLayerId = visibleDatasetId
          ? renderer?.getDatasetFillLayerId(visibleDatasetId)
          : null;

        if (!fillLayerId) {
          NotificationService.error('No visible polygon layer to query. Toggle a dataset on first.');
          return;
        }

        const rect = map.getContainer().getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const hits = map.queryRenderedFeatures([x, y], { layers: [fillLayerId] });

        if (!hits.length) {
          NotificationService.info('No polygon there. Click inside a polygon feature.');
          return;
        }

        const featureId = hits[0].properties?.__feature_id as string | undefined;
        if (!featureId) {
          console.error('[IntersectsQueryPanel] Clicked feature has no __feature_id', hits[0]);
          NotificationService.error('That feature is missing an id and cannot be queried.');
          return;
        }

        const featureName = (hits[0].properties?.name as string) ?? 'selected feature';
        setSourceFeature({ id: featureId, name: featureName });
        executeQuery(featureId, featureName);
      };

      map.getCanvasContainer().addEventListener('click', handler, { capture: true });
      clickHandlerRef.current = handler;
    }

    return () => {
      if (clickHandlerRef.current && map) {
        map.getCanvasContainer().removeEventListener('click', clickHandlerRef.current, {
          capture: true,
        });
        clickHandlerRef.current = null;
        map.getCanvas().style.cursor = '';
      }
    };
  }, [active, visibleDatasetId, executeQuery, setSourceFeature]);

  // Stand down if another query mode takes over.
  useEffect(() => {
    if ((nearbyActive || containsActive) && active) {
      EarthEngine.getInstance().getMapLibreDatasetRenderer()?.clearIntersectsResults();
      deactivate();
    }
  }, [nearbyActive, containsActive, active, deactivate]);

  const handleToggle = () => {
    const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
    if (active) {
      renderer?.clearIntersectsResults();
      deactivate();
    } else {
      // Take exclusive ownership of map clicks.
      if (useNearbyQueryStore.getState().active) {
        renderer?.clearNearbyResults();
        useNearbyQueryStore.getState().deactivate();
      }
      if (useContainsQueryStore.getState().active) {
        renderer?.clearContainsResults();
        useContainsQueryStore.getState().deactivate();
      }
      activate();
    }
  };

  const handleClear = () => {
    EarthEngine.getInstance().getMapLibreDatasetRenderer()?.clearIntersectsResults();
    clear();
  };

  const targetOptions = datasets.filter((d) => d.id !== visibleDatasetId);

  return (
    <div className="border-t pt-3 mt-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase text-muted-foreground tracking-tight">
          Intersection Query
        </span>
        <Button
          variant={active ? 'default' : 'outline'}
          size="sm"
          className="h-7 text-xs gap-1.5"
          onClick={handleToggle}
          aria-label={active ? 'Deactivate intersects query' : 'Activate intersects query'}
        >
          <Layers className="w-3.5 h-3.5" />
          {active ? 'Cancel' : 'Query Intersects'}
        </Button>
      </div>

      {active && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground whitespace-nowrap">Against:</label>
            <select
              value={targetDatasetId ?? ''}
              onChange={(e) => setTargetDatasetId(e.target.value || null)}
              className="flex-1 h-7 px-2 text-xs rounded-md bg-zinc-800 border border-zinc-700 text-zinc-200 focus:outline-none focus:border-zinc-500"
              aria-label="Target dataset to intersect against"
            >
              {targetOptions.length === 0 && <option value="">No other dataset</option>}
              {targetOptions.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          <p className="text-xs text-muted-foreground">
            {sourceFeature
              ? `Source: ${sourceFeature.name}`
              : 'Click a polygon on the map to find what it intersects.'}
          </p>

          {loading && <p className="text-xs text-blue-400 animate-pulse">Querying...</p>}

          {results && (
            <div className="flex items-center justify-between">
              <p className="text-xs text-cyan-400 font-medium">
                {results.features.length} feature{results.features.length !== 1 ? 's' : ''}{' '}
                intersecting
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs gap-1 text-muted-foreground hover:text-zinc-200"
                onClick={handleClear}
                aria-label="Clear intersection results"
              >
                <X className="w-3 h-3" />
                Clear
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
