import { create } from 'zustand';
import type { FeatureCollection, Geometry } from 'geojson';

interface NearbyQueryState {
  /** Whether "Query Nearby" mode is active (map click captures a point). */
  active: boolean;
  /** The lon/lat captured from the last map click. */
  queryPoint: { lon: number; lat: number } | null;
  /** Search radius in meters. */
  radius: number;
  /** GeoJSON FeatureCollection returned from the API. */
  results: FeatureCollection<Geometry> | null;
  /** Whether a query is currently in-flight. */
  loading: boolean;

  activate: () => void;
  deactivate: () => void;
  setQueryPoint: (lon: number, lat: number) => void;
  setRadius: (radius: number) => void;
  setResults: (results: FeatureCollection<Geometry> | null) => void;
  setLoading: (loading: boolean) => void;
  clear: () => void;
}

export const useNearbyQueryStore = create<NearbyQueryState>((set) => ({
  active: false,
  queryPoint: null,
  radius: 10000,
  results: null,
  loading: false,

  activate: () => set({ active: true, queryPoint: null, results: null }),
  deactivate: () => set({ active: false, queryPoint: null, results: null }),
  setQueryPoint: (lon, lat) => set({ queryPoint: { lon, lat } }),
  setRadius: (radius) => set({ radius }),
  setResults: (results) => set({ results, loading: false }),
  setLoading: (loading) => set({ loading }),
  clear: () => set({ queryPoint: null, results: null }),
}));
