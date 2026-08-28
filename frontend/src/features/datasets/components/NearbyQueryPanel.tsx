import { useCallback, useEffect, useRef } from 'react';
import { Crosshair, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNearbyQueryStore } from '../../earth/stores/useNearbyQueryStore';
import { useLayerStore } from '../../earth/stores/useLayerStore';
import { useProjectStore } from '../../../stores/useProjectStore';
import { EarthEngine } from '../../earth/services/EarthEngine';
import { NotificationService } from '../../../shared/services/notification.service';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export function NearbyQueryPanel() {
  const active = useNearbyQueryStore((s) => s.active);
  const queryPoint = useNearbyQueryStore((s) => s.queryPoint);
  const radius = useNearbyQueryStore((s) => s.radius);
  const results = useNearbyQueryStore((s) => s.results);
  const loading = useNearbyQueryStore((s) => s.loading);

  const activate = useNearbyQueryStore((s) => s.activate);
  const deactivate = useNearbyQueryStore((s) => s.deactivate);
  const setQueryPoint = useNearbyQueryStore((s) => s.setQueryPoint);
  const setRadius = useNearbyQueryStore((s) => s.setRadius);
  const setResults = useNearbyQueryStore((s) => s.setResults);
  const setLoading = useNearbyQueryStore((s) => s.setLoading);
  const clear = useNearbyQueryStore((s) => s.clear);

  const clickHandlerRef = useRef<((e: MouseEvent) => void) | null>(null);

  // Get the first visible dataset ID to query against
  const visibleDatasetId = useLayerStore((s) => {
    const visible = s.layers.find((l) => l.visible && l.category === 'geojson');
    return visible?.id ?? null;
  });

  const projectId = useProjectStore((s) => s.activeProjectId);

  // Execute the actual nearby query
  const executeQuery = useCallback(
    async (lon: number, lat: number, radiusM: number) => {
      if (!projectId || !visibleDatasetId) {
        NotificationService.error('No visible dataset to query. Toggle a dataset on first.');
        return;
      }

      setLoading(true);

      try {
        const url = `${API_BASE_URL}/projects/${projectId}/datasets/${visibleDatasetId}/query/nearby?lon=${lon}&lat=${lat}&radius_meters=${radiusM}`;
        const res = await fetch(url);

        if (!res.ok) {
          const errText = await res.text();
          throw new Error(errText);
        }

        const geojson = await res.json();
        setResults(geojson);

        // Render the results on the map
        const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
        renderer?.showNearbyResults(geojson, { lon, lat });

        const count = geojson.features?.length ?? 0;
        NotificationService.success(
          `${count} feature${count !== 1 ? 's' : ''} found within ${radiusM.toLocaleString()}m`
        );
      } catch (err) {
        console.error('Nearby query failed:', err);
        NotificationService.error('Nearby query failed. Check console for details.');
        setResults(null);
      }
    },
    [projectId, visibleDatasetId, setResults, setLoading]
  );

  // Register / unregister the map click handler when mode is toggled
  useEffect(() => {
    const map = EarthEngine.getInstance().getMap();
    console.log('[NearbyQueryPanel] useEffect triggered. active:', active, 'map exists:', !!map);
    if (!map) {
      console.warn('[NearbyQueryPanel] Map is not available yet.');
      return;
    }

    if (active) {
      console.log('[NearbyQueryPanel] Activating query mode, attaching click handler');
      // Set crosshair cursor
      map.getCanvas().style.cursor = 'crosshair';

      const handler = (e: MouseEvent) => {
        console.log('[NearbyQueryPanel] Canvas native click', e.clientX, e.clientY);
        
        // Convert screen pixel to lng/lat
        const rect = map.getContainer().getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const lngLat = map.unproject([x, y]);
        
        console.log('[NearbyQueryPanel] Unprojected to', lngLat);
        setQueryPoint(lngLat.lng, lngLat.lat);
        executeQuery(lngLat.lng, lngLat.lat, useNearbyQueryStore.getState().radius);
      };

      map.getCanvasContainer().addEventListener('click', handler, { capture: true });
      clickHandlerRef.current = handler;
    }

    return () => {
      if (clickHandlerRef.current && map) {
        console.log('[NearbyQueryPanel] Cleaning up click handler');
        map.getCanvasContainer().removeEventListener('click', clickHandlerRef.current, { capture: true });
        clickHandlerRef.current = null;
        map.getCanvas().style.cursor = '';
      }
    };
  }, [active, executeQuery, setQueryPoint]);

  const handleToggle = () => {
    if (active) {
      // Deactivate and clear results from map
      const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
      renderer?.clearNearbyResults();
      deactivate();
    } else {
      activate();
    }
  };

  const handleClear = () => {
    const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
    renderer?.clearNearbyResults();
    clear();
  };

  return (
    <div className="border-t pt-3 mt-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase text-muted-foreground tracking-tight">
          Spatial Query
        </span>
        <Button
          variant={active ? 'default' : 'outline'}
          size="sm"
          className="h-7 text-xs gap-1.5"
          onClick={handleToggle}
          aria-label={active ? 'Deactivate nearby query' : 'Activate nearby query'}
        >
          <Crosshair className="w-3.5 h-3.5" />
          {active ? 'Cancel' : 'Query Nearby'}
        </Button>
      </div>

      {active && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground whitespace-nowrap">
              Radius (m):
            </label>
            <input
              type="number"
              min={1}
              value={radius}
              onChange={(e) => setRadius(Math.max(1, Number(e.target.value)))}
              className="flex-1 h-7 px-2 text-xs rounded-md bg-zinc-800 border border-zinc-700 text-zinc-200 focus:outline-none focus:border-zinc-500"
              aria-label="Search radius in meters"
            />
          </div>

          <p className="text-xs text-muted-foreground">
            {queryPoint
              ? `Queried: (${queryPoint.lon.toFixed(4)}, ${queryPoint.lat.toFixed(4)})`
              : 'Click on the map to select a query point.'}
          </p>

          {loading && (
            <p className="text-xs text-blue-400 animate-pulse">Querying...</p>
          )}

          {results && (
            <div className="flex items-center justify-between">
              <p className="text-xs text-emerald-400 font-medium">
                {results.features.length} feature{results.features.length !== 1 ? 's' : ''} found
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs gap-1 text-muted-foreground hover:text-zinc-200"
                onClick={handleClear}
                aria-label="Clear query results"
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
