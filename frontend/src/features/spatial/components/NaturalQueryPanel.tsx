import { useCallback, useRef, type KeyboardEvent } from 'react';
import { Search, X, Loader2, MapPin, AlertCircle, Sparkles } from 'lucide-react';
import { useNaturalQueryStore } from '../stores/useNaturalQueryStore';
import type { PlaceCandidate } from '../stores/useNaturalQueryStore';
import { useProjectStore } from '@/stores/useProjectStore';
import { EarthEngine } from '@/features/earth/services/EarthEngine';
import { NotificationService } from '@/shared/services/notification.service';
import type { FeatureCollection, Geometry } from 'geojson';

/**
 * A natural-language query interface for the TerraMind spatial engine.
 *
 * The user types a question, the backend interprets it with Claude, validates
 * the intent, runs the existing spatial engine, and returns GeoJSON that this
 * component renders on the existing map.
 *
 * No geographic computation happens here. This component is purely I/O:
 * it sends the question and renders the answer.
 */
export function NaturalQueryPanel() {
  const query = useNaturalQueryStore((s) => s.query);
  const loading = useNaturalQueryStore((s) => s.loading);
  const result = useNaturalQueryStore((s) => s.result);
  const error = useNaturalQueryStore((s) => s.error);
  const setQuery = useNaturalQueryStore((s) => s.setQuery);
  const submit = useNaturalQueryStore((s) => s.submit);
  const clear = useNaturalQueryStore((s) => s.clear);

  const projectId = useProjectStore((s) => s.activeProjectId);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = useCallback(async () => {
    if (!projectId) {
      NotificationService.error('Select a project first.');
      return;
    }
    if (!query.trim()) return;

    // Clear any previous map results before submitting.
    const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
    renderer?.clearNaturalQueryResults();

    await submit(projectId);

    // After submitting, check the store for the result (it was set during submit).
    const state = useNaturalQueryStore.getState();

    if (state.result?.status === 'ok' && state.result.result) {
      const geojson = state.result.result as FeatureCollection<Geometry>;
      const focus = state.result.focus ?? undefined;

      // Render results on the map.
      renderer?.showNaturalQueryResults(geojson, focus);

      // Fit the map to the result bounds.
      const map = EarthEngine.getInstance().getMap();
      if (map && geojson.features.length > 0) {
        const coords: [number, number][] = [];
        for (const feature of geojson.features) {
          extractCoords(feature.geometry, coords);
        }
        if (focus) coords.push([focus.lon, focus.lat]);

        if (coords.length > 0) {
          const bounds = coords.reduce(
            (b, [lng, lat]) => {
              b[0] = Math.min(b[0], lng);
              b[1] = Math.min(b[1], lat);
              b[2] = Math.max(b[2], lng);
              b[3] = Math.max(b[3], lat);
              return b;
            },
            [Infinity, Infinity, -Infinity, -Infinity] as [number, number, number, number],
          );
          map.fitBounds(
            [
              [bounds[0], bounds[1]],
              [bounds[2], bounds[3]],
            ],
            { padding: 60, maxZoom: 16, duration: 1000 },
          );
        }
      }

      const count = geojson.features.length;
      NotificationService.success(
        `${count} feature${count !== 1 ? 's' : ''} found`,
      );
    }
  }, [projectId, query, submit]);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleClear = () => {
    const renderer = EarthEngine.getInstance().getMapLibreDatasetRenderer();
    renderer?.clearNaturalQueryResults();
    clear();
  };

  const featureCount = result?.result?.features?.length ?? 0;
  const hasResults = result?.status === 'ok' && result.result != null;
  const isAmbiguous = result?.status === 'ambiguous';
  const isUnresolved = result?.status === 'unresolved';

  return (
    <div
      id="natural-query-panel"
      className="absolute top-4 left-1/2 -translate-x-1/2 z-30 pointer-events-auto w-full max-w-xl px-4"
    >
      {/* ── Search bar ── */}
      <div
        className="flex items-center gap-2 bg-zinc-950/90 backdrop-blur-lg border border-zinc-800 rounded-xl shadow-2xl px-4 py-2.5 transition-all focus-within:border-emerald-600/60 focus-within:shadow-emerald-500/10"
      >
        <Sparkles className="h-4 w-4 text-emerald-500 shrink-0" />
        <input
          ref={inputRef}
          id="nlq-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a geographic question… e.g. &quot;Show hospitals within 2 km of Lalbagh&quot;"
          disabled={loading}
          className="flex-1 bg-transparent text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none disabled:opacity-50"
          aria-label="Natural language query"
          autoComplete="off"
          spellCheck={false}
        />
        {loading ? (
          <Loader2 className="h-4 w-4 text-emerald-400 animate-spin shrink-0" />
        ) : query.trim() ? (
          <button
            onClick={handleClear}
            className="text-zinc-500 hover:text-zinc-300 transition-colors"
            aria-label="Clear query"
          >
            <X className="h-4 w-4" />
          </button>
        ) : null}
        <button
          id="nlq-submit"
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
          className="flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white text-xs font-medium px-3 py-1.5 transition-colors shrink-0"
          aria-label="Submit query"
        >
          <Search className="h-3.5 w-3.5" />
          Ask
        </button>
      </div>

      {/* ── Result / error / status card ── */}
      {(hasResults || isAmbiguous || isUnresolved || error) && (
        <div className="mt-2 bg-zinc-950/90 backdrop-blur-lg border border-zinc-800 rounded-xl shadow-xl px-4 py-3 space-y-2 max-h-64 overflow-auto">
          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 text-red-400">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <p className="text-xs leading-relaxed">{error}</p>
            </div>
          )}

          {/* Success */}
          {hasResults && result && (
            <>
              <p className="text-xs text-emerald-400 font-medium">
                {result.answer}
              </p>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-zinc-500 uppercase tracking-wide">
                  {featureCount} feature{featureCount !== 1 ? 's' : ''} on map
                </span>
                {result.interpretation && (
                  <span className="text-[10px] text-zinc-600 font-mono">
                    {result.interpretation.operation}
                    {result.interpretation.distance_meters
                      ? ` · ${result.interpretation.distance_meters >= 1000 ? `${result.interpretation.distance_meters / 1000}km` : `${result.interpretation.distance_meters}m`}`
                      : ''}
                  </span>
                )}
              </div>
            </>
          )}

          {/* Ambiguous */}
          {isAmbiguous && result && (
            <>
              <div className="flex items-start gap-2 text-amber-400">
                <MapPin className="h-4 w-4 shrink-0 mt-0.5" />
                <p className="text-xs leading-relaxed">{result.answer}</p>
              </div>
              {result.candidates.length > 0 && (
                <ul className="space-y-1 ml-6">
                  {result.candidates.map((c: PlaceCandidate) => (
                    <li key={c.feature_id} className="text-xs text-zinc-400">
                      <span className="text-zinc-200">{c.feature_name}</span>
                      {c.category && (
                        <span className="text-zinc-600 ml-1">({c.category})</span>
                      )}
                      <span className="text-zinc-700 ml-1">
                        in {c.dataset_name}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}

          {/* Unresolved */}
          {isUnresolved && result && (
            <div className="flex items-start gap-2 text-zinc-400">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <p className="text-xs leading-relaxed">{result.answer}</p>
            </div>
          )}

          {/* Clear button */}
          <button
            onClick={handleClear}
            className="text-[10px] text-zinc-600 hover:text-zinc-400 transition-colors uppercase tracking-wider"
          >
            Clear results
          </button>
        </div>
      )}
    </div>
  );
}

/** Recursively extract [lon, lat] pairs from any GeoJSON geometry for bounds. */
function extractCoords(
  geometry: GeoJSON.Geometry | null,
  out: [number, number][],
) {
  if (!geometry) return;
  switch (geometry.type) {
    case 'Point':
      out.push(geometry.coordinates as [number, number]);
      break;
    case 'MultiPoint':
    case 'LineString':
      for (const c of geometry.coordinates) out.push(c as [number, number]);
      break;
    case 'MultiLineString':
    case 'Polygon':
      for (const ring of geometry.coordinates)
        for (const c of ring) out.push(c as [number, number]);
      break;
    case 'MultiPolygon':
      for (const poly of geometry.coordinates)
        for (const ring of poly) for (const c of ring) out.push(c as [number, number]);
      break;
    case 'GeometryCollection':
      for (const g of geometry.geometries) extractCoords(g, out);
      break;
  }
}
