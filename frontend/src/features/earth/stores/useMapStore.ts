import { create } from 'zustand'
import { type EngineState } from '../services/EarthEngine'

type MapStoreState = {
  engineState: EngineState
  isEngineReady: boolean
  setEngineState: (state: EngineState) => void
  setEngineReady: (ready: boolean) => void
}

export const useMapStore = create<MapStoreState>((set) => ({
  engineState: 'uninitialized',
  isEngineReady: false,
  setEngineState: (state) => set({ engineState: state }),
  setEngineReady: (ready) => set({ isEngineReady: ready }),
}))
