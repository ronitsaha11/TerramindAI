import { create } from 'zustand';
import type { FeatureCollection, Geometry } from 'geojson';

/** The polygon feature a containment query is anchored to. */
interface SourceFeature {
  id: string;
  name: string;
}

interface ContainsQueryState {
  /** Whether "Query Contains" mode is active (map click picks a polygon). */
  active: boolean;
  /** The polygon feature captured from the last map click. */
  sourceFeature: SourceFeature | null;
  /** GeoJSON FeatureCollection returned from the API. */
  results: FeatureCollection<Geometry> | null;
  /** Whether a query is currently in-flight. */
  loading: boolean;

  activate: () => void;
  deactivate: () => void;
  setSourceFeature: (feature: SourceFeature | null) => void;
  setResults: (results: FeatureCollection<Geometry> | null) => void;
  setLoading: (loading: boolean) => void;
  clear: () => void;
}

export const useContainsQueryStore = create<ContainsQueryState>((set) => ({
  active: false,
  sourceFeature: null,
  results: null,
  loading: false,

  activate: () => set({ active: true, sourceFeature: null, results: null }),
  deactivate: () => set({ active: false, sourceFeature: null, results: null, loading: false }),
  setSourceFeature: (sourceFeature) => set({ sourceFeature }),
  setResults: (results) => set({ results, loading: false }),
  setLoading: (loading) => set({ loading }),
  clear: () => set({ sourceFeature: null, results: null }),
}));
