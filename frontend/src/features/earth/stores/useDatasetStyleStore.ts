import { create } from 'zustand';

interface DatasetStyleState {
  /** datasetId -> the property currently being coloured by, if any. */
  styleProperty: Record<string, string | null>;

  setStyleProperty: (datasetId: string, property: string | null) => void;
  clearDataset: (datasetId: string) => void;
}

export const useDatasetStyleStore = create<DatasetStyleState>((set) => ({
  styleProperty: {},

  setStyleProperty: (datasetId, property) =>
    set((s) => ({ styleProperty: { ...s.styleProperty, [datasetId]: property } })),

  clearDataset: (datasetId) =>
    set((s) => {
      const next = { ...s.styleProperty };
      delete next[datasetId];
      return { styleProperty: next };
    }),
}));
