import { type Map as MapLibreMap } from 'maplibre-gl'
import { type Coordinate, type BoundingBox } from '../types/coordinate.types'

/** 
 * ProjectionService exposes renderer viewport state through 
 * renderer-independent TerraMind types. 
 * It hides all MapLibre-specific APIs from callers.
 */
export class ProjectionService {
  private _map: MapLibreMap | null = null

  bind(map: MapLibreMap): void {
    this._map = map
  }

  unbind(): void {
    this._map = null
  }

  /** Get the geographic bounds of the current viewport. */
  viewportBounds(): BoundingBox | null {
    if (!this._map) return null
    const bounds = this._map.getBounds()
    return {
      west: bounds.getWest(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      north: bounds.getNorth(),
    }
  }

  /** Alias of viewportBounds for semantic clarity. */
  visibleBounds(): BoundingBox | null {
    return this.viewportBounds()
  }

  /** Get the geographic center of the current viewport. */
  currentCenter(): Coordinate | null {
    if (!this._map) return null
    const c = this._map.getCenter()
    return { longitude: c.lng, latitude: c.lat }
  }

  /** Get the current zoom level. */
  currentZoom(): number | null {
    if (!this._map) return null
    return this._map.getZoom()
  }

  /** Get the current bearing in degrees. */
  currentBearing(): number | null {
    if (!this._map) return null
    return this._map.getBearing()
  }

  /** Get the current pitch in degrees. */
  currentPitch(): number | null {
    if (!this._map) return null
    return this._map.getPitch()
  }
}
