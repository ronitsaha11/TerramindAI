import { type Map as MapLibreMap } from 'maplibre-gl'
import { TERRAIN_CONFIG } from '../config/terrain.config'

/** 
 * A decoupled snapshot of environment state.
 * Prevents direct Zustand imports inside the renderer tier.
 */
export interface EnvironmentStateSnapshot {
  terrainEnabled: boolean
  skyEnabled: boolean
  fogEnabled: boolean
  terrainExaggeration: number
}

/**
 * EnvironmentController is the canonical owner of DEM sources,
 * terrain lifecycles, and sky lifecycles.
 */
export class EnvironmentController {
  private _map: MapLibreMap | null = null
  private _state: EnvironmentStateSnapshot | null = null

  initialize(map: MapLibreMap): void {
    if (this._map) return
    this._map = map

    // Register the DEM source if it doesn't already exist
    if (!map.getSource(TERRAIN_CONFIG.SOURCE_ID)) {
      map.addSource(TERRAIN_CONFIG.SOURCE_ID, TERRAIN_CONFIG.SOURCE)
    }

    // Apply any pending state
    if (this._state) {
      this.sync(this._state)
    }
  }

  /** Synchronize renderer state with the provided environment snapshot. */
  sync(state: EnvironmentStateSnapshot): void {
    this._state = state
    if (!this._map) return

    this._syncTerrain(state)
    this._syncSky(state)
    this._syncFog(state)
  }

  /** Tear down terrain and sources. */
  destroy(): void {
    if (this._map) {
      this._map.setTerrain(null)
      // Attempt safe removal of the DEM source
      try {
        if (this._map.getSource(TERRAIN_CONFIG.SOURCE_ID)) {
          this._map.removeSource(TERRAIN_CONFIG.SOURCE_ID)
        }
      } catch {
        // Safe to ignore on destroy
      }
    }
    this._map = null
    this._state = null
  }

  private _syncTerrain(state: EnvironmentStateSnapshot): void {
    if (!this._map) return
    if (state.terrainEnabled) {
      this._map.setTerrain({
        source: TERRAIN_CONFIG.SOURCE_ID,
        exaggeration: state.terrainExaggeration,
      })
    } else {
      this._map.setTerrain(null)
    }
  }

  private _syncSky(state: EnvironmentStateSnapshot): void {
    if (!this._map) return
    // Note: Mapbox GL JS natively supports 'sky' via map.setSky() or addLayer({ type: 'sky' }).
    // MapLibre GL JS handles sky/background differently.
    // This is the foundation method for when the MapLibre sky plugin or native layer is integrated.
    void state.skyEnabled
  }

  private _syncFog(state: EnvironmentStateSnapshot): void {
    if (!this._map) return
    void state.fogEnabled
  }
}
