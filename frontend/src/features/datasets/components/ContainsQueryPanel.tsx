import { useCallback, useEffect, useRef } from 'react';
import { Square, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useContainsQueryStore } from '../../earth/stores/useContainsQueryStore';
import { useNearbyQueryStore } from '../../earth/stores/useNearbyQueryStore';
import { useLayerStore } from '../../earth/stores/useLayerStore';
import { useProjectStore } from '../../../stores/useProjectStore';
import { EarthEngine } from '../../earth/services/EarthEngine';
import { NotificationService } from '../../../shared/services/notification.service';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export function ContainsQueryPanel() {
  const active = useContainsQueryStore((s) => s.active);
  const sourceFeature = useContainsQueryStore((s) => s.sourceFeature);
  const results = useContainsQueryStore((s) => s.results);
  const loading = useContainsQueryStore((s) => s.loading);

  const activate = useContainsQueryStore((s) => s.activate);
  const deactivate = useContainsQueryStore((s) => s.deactivate);
  const setSourceFeature = useContainsQueryStore((s) => s.setSourceFeature);
  const setResults = useContainsQueryStore((s) => s.setResults);
  const setLoading = useContainsQueryStore((s) => s.setLoading);
  const clear = useContainsQueryStore((s) => s.clear);

  // Nearby query owns a capture-phase canvas click handler too, so the two
  // modes must never be active at the same time.
  const nearbyActive = useNearbyQueryStore((s) => s.active);

  const clickHandlerRef = useRef<((e: MouseEvent) => void) | null>(null);

  const visibleDatasetId = useLayerStore((s) => {
    const visible = s.layers.find((l) => l.visible && l.category === 'geojson');
    return visible?.id ?? null;
  });

  const projectId = useProjectStore((s) => s.activeProjectId);

  const executeQuery = useCallback(
    async (featureId: string, featureName: string) => {
      if (!projectId || !visibleDatasetId) {
        NotificationService.error('No visible dataset to query. Toggle a dataset on first.');
        return;
      }

      setLoading(true);

      try {
        const url = `${API_BASE_URL}/projects/${projectId}/datasets/${visibleDatasetId}/query/contains?feature_id=${featureId}`;
        const res = await fetch(url);

        if (!res.ok) {
          const errText = await res.text();
          throw new Error(errText);
        }

        const geojson = await res.json();
        setResults(geojson);

        const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
        const source = renderer?.getFeatureById(visibleDatasetId, featureId);
        renderer?.showContainsResults(geojson, source);

        const count = geojson.features?.length ?? 0;
        NotificationService.success(
          `${count} feature${count !== 1 ? 's' : ''} contained within ${featureName}`
        );
      } catch (err) {
        console.error('Contains query failed:', err);
        NotificationService.error('Contains query failed. Check console for details.');
        setResults(null);
      }
    },
    [projectId, visibleDatasetId, setResults, setLoading]
  );

  // Register / unregister the map click handler when mode is toggled
  useEffect(() => {
    const map = EarthEngine.getInstance().getMap();
    if (!map) {
      console.warn('[ContainsQueryPanel] Map is not available yet.');
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

        // Scoped to the dataset's own fill layer so result highlights are
        // never picked up as click targets.
        const hits = map.queryRenderedFeatures([x, y], { layers: [fillLayerId] });

        if (!hits.length) {
          NotificationService.info('No polygon there. Click inside a polygon feature.');
          return;
        }

        const featureId = hits[0].properties?.__feature_id as string | undefined;
        if (!featureId) {
          console.error('[ContainsQueryPanel] Clicked feature has no __feature_id', hits[0]);
          NotificationService.error('That feature is missing an id and cannot be queried.');
          return;
        }

        const featureName = (hits[0].properties?.name as string) ?? 'selected polygon';
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

  // Stand down if nearby query mode takes over.
  useEffect(() => {
    if (nearbyActive && active) {
      EarthEngine.getInstance().getMapLibreDatasetRenderer()?.clearContainsResults();
      deactivate();
    }
  }, [nearbyActive, active, deactivate]);

  const handleToggle = () => {
    const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
    if (active) {
      renderer?.clearContainsResults();
      deactivate();
    } else {
      // Take exclusive ownership of map clicks.
      if (useNearbyQueryStore.getState().active) {
        renderer?.clearNearbyResults();
        useNearbyQueryStore.getState().deactivate();
      }
      activate();
    }
  };

  const handleClear = () => {
    EarthEngine.getInstance().getMapLibreDatasetRenderer()?.clearContainsResults();
    clear();
  };

  return (
    <div className="border-t pt-3 mt-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase text-muted-foreground tracking-tight">
          Containment Query
        </span>
        <Button
          variant={active ? 'default' : 'outline'}
          size="sm"
          className="h-7 text-xs gap-1.5"
          onClick={handleToggle}
          aria-label={active ? 'Deactivate contains query' : 'Activate contains query'}
        >
          <Square className="w-3.5 h-3.5" />
          {active ? 'Cancel' : 'Query Contains'}
        </Button>
      </div>

      {active && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">
            {sourceFeature
              ? `Source: ${sourceFeature.name}`
              : 'Click a polygon on the map to find what it contains.'}
          </p>

          {loading && <p className="text-xs text-blue-400 animate-pulse">Querying...</p>}

          {results && (
            <div className="flex items-center justify-between">
              <p className="text-xs text-emerald-400 font-medium">
                {results.features.length} feature{results.features.length !== 1 ? 's' : ''} contained
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs gap-1 text-muted-foreground hover:text-zinc-200"
                onClick={handleClear}
                aria-label="Clear containment results"
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
