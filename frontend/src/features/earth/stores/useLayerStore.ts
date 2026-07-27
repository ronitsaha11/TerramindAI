import { create } from 'zustand'
import { type LayerState, type LayerId } from '../types/layer.types'

type LayerStoreState = {
  /** Ordered snapshot of all registered layers — LayerManager owns mutation. */
  layers: LayerState[]
  /** Ordered list of layer IDs (top = front of rendering stack). */
  layerOrder: LayerId[]
  /** Currently selected layer ID, or null. */
  selectedLayer: LayerId | null
  setLayers: (layers: LayerState[], order: LayerId[]) => void
  selectLayer: (id: LayerId | null) => void
  reset: () => void
}

export const useLayerStore = create<LayerStoreState>((set) => ({
  layers: [],
  layerOrder: [],
  selectedLayer: null,
  setLayers: (layers, layerOrder) => set({ layers, layerOrder }),
  selectLayer: (selectedLayer) => set({ selectedLayer }),
  reset: () => set({ layers: [], layerOrder: [], selectedLayer: null }),
}))
