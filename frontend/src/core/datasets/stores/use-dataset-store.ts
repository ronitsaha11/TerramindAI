import { create } from 'zustand';
import type { DatasetStore, DatasetStoreState } from './dataset-store.types';
import type { IDatasetRegistry } from '../registry/dataset-registry.interface';
import type { IDataset } from '../models/dataset';

// Initial state object for easy reset
const initialState: DatasetStoreState = {
  datasets: {},
  datasetIds: [],
  activeDatasetId: null,
  initialized: false,
  syncing: false,
};

/**
 * Reference to hold the registry unsubscribe callback.
 * Kept outside the state to avoid Zustand tracking non-serializable data.
 */
let unsubscribeRegistry: (() => void) | null = null;

/**
 * Zustand store mirroring the Dataset Registry for React consumption.
 * Owns UI state (e.g., activeDatasetId) but never mutates datasets directly.
 */
export const useDatasetStore = create<DatasetStore>((set, get) => ({
  ...initialState,

  initialize: (registry: IDatasetRegistry) => {
    const { initialized } = get();

    if (initialized) {
      console.warn('DatasetStore is already initialized.');
      return;
    }

    // Define the internal synchronization routine
    const _sync = () => {
      set({ syncing: true });

      try {
        const datasetList = registry.list();
        const datasetsRecord: Record<string, IDataset> = {};
        const datasetIdsArray: string[] = [];

        datasetList.forEach((dataset) => {
          datasetsRecord[dataset.id] = dataset;
          datasetIdsArray.push(dataset.id);
        });

        // Atomically update state
        set({
          datasets: Object.freeze(datasetsRecord),
          datasetIds: Object.freeze(datasetIdsArray),
          syncing: false,
        });
      } catch (error) {
        console.error('DatasetStore synchronization failed:', error);
        set({ syncing: false });
      }
    };

    // Perform initial synchronization
    _sync();

    // Subscribe to registry changes
    unsubscribeRegistry = registry.subscribe(_sync);

    // Mark as initialized
    set({ initialized: true });
  },

  setActiveDataset: (id: string) => {
    // Only allow setting active if the dataset actually exists in the mirrored state
    const { datasets } = get();
    if (datasets[id]) {
      set({ activeDatasetId: id });
    } else {
      console.warn(`Cannot set active dataset: ID '${id}' not found in store.`);
    }
  },

  clearActiveDataset: () => {
    set({ activeDatasetId: null });
  },

  destroy: () => {
    if (unsubscribeRegistry) {
      unsubscribeRegistry();
      unsubscribeRegistry = null;
    }
    set(initialState);
  }
}));

// ----------------------------------------------------
// Typed Selectors (Helper exports to minimize re-renders)
// ----------------------------------------------------

export const getAllDatasets = (state: DatasetStore) => Object.values(state.datasets);
export const getDatasetIds = (state: DatasetStore) => state.datasetIds;
export const getDatasetCount = (state: DatasetStore) => state.datasetIds.length;
export const getActiveDataset = (state: DatasetStore) => 
  state.activeDatasetId ? state.datasets[state.activeDatasetId] : null;
export const hasDatasets = (state: DatasetStore) => state.datasetIds.length > 0;
export const getDatasetById = (id: string) => (state: DatasetStore) => state.datasets[id];
