import { create } from 'zustand';
import type { FeatureCollection, Geometry } from 'geojson';

/** The feature a cross-dataset intersection query is anchored to. */
interface SourceFeature {
  id: string;
  name: string;
}

interface IntersectsQueryState {
  /** Whether "Query Intersects" mode is active (map click picks a feature). */
  active: boolean;
  /** Dataset to search for features intersecting the clicked one. */
  targetDatasetId: string | null;
  /** The feature captured from the last map click. */
  sourceFeature: SourceFeature | null;
  /** GeoJSON FeatureCollection returned from the API. */
  results: FeatureCollection<Geometry> | null;
  /** Whether a query is currently in-flight. */
  loading: boolean;

  activate: () => void;
  deactivate: () => void;
  setTargetDatasetId: (id: string | null) => void;
  setSourceFeature: (feature: SourceFeature | null) => void;
  setResults: (results: FeatureCollection<Geometry> | null) => void;
  setLoading: (loading: boolean) => void;
  clear: () => void;
}

export const useIntersectsQueryStore = create<IntersectsQueryState>((set) => ({
  active: false,
  targetDatasetId: null,
  sourceFeature: null,
  results: null,
  loading: false,

  // The chosen target dataset survives toggling the mode off and on.
  activate: () => set({ active: true, sourceFeature: null, results: null }),
  deactivate: () => set({ active: false, sourceFeature: null, results: null, loading: false }),
  setTargetDatasetId: (targetDatasetId) => set({ targetDatasetId }),
  setSourceFeature: (sourceFeature) => set({ sourceFeature }),
  setResults: (results) => set({ results, loading: false }),
  setLoading: (loading) => set({ loading }),
  clear: () => set({ sourceFeature: null, results: null }),
}));
