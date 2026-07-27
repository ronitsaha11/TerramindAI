import { create } from 'zustand'

export type EnvironmentState = {
  terrainEnabled: boolean
  skyEnabled: boolean
  fogEnabled: boolean
  terrainExaggeration: number
  toggleTerrain: () => void
  toggleSky: () => void
  toggleFog: () => void
  setTerrainExaggeration: (exaggeration: number) => void
}

export const useEnvironmentStore = create<EnvironmentState>((set) => ({
  terrainEnabled: false,
  skyEnabled: false,
  fogEnabled: false,
  terrainExaggeration: 1.5,
  toggleTerrain: () => set((state) => ({ terrainEnabled: !state.terrainEnabled })),
  toggleSky: () => set((state) => ({ skyEnabled: !state.skyEnabled })),
  toggleFog: () => set((state) => ({ fogEnabled: !state.fogEnabled })),
  setTerrainExaggeration: (exaggeration) => set({ terrainExaggeration: exaggeration }),
}))
