import { create } from 'zustand';
import type { ViewportQueryResult, VisibleDatasetResult } from '../../earth/types/viewport-query.types';

export interface SpatialState {
  visibleFeaturesCount: number;
  visibleDatasets: ReadonlyArray<VisibleDatasetResult>;
  isCalculating: boolean;
  
  setVisibleResult: (result: ViewportQueryResult) => void;
  setCalculating: (isCalculating: boolean) => void;
}

export const useSpatialStore = create<SpatialState>((set) => ({
  visibleFeaturesCount: 0,
  visibleDatasets: [],
  isCalculating: false,

  setVisibleResult: (result) => set({
    visibleFeaturesCount: result.totalVisibleFeatures,
    visibleDatasets: result.datasets,
    isCalculating: false
  }),

  setCalculating: (isCalculating) => set({ isCalculating })
}));
