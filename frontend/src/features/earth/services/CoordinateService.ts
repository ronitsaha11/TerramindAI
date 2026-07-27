import { type Map as MapLibreMap } from 'maplibre-gl'
import { distance } from '@turf/distance'
import { point } from '@turf/helpers'
import { 
  type Coordinate, 
  type ScreenCoordinate, 
  type BoundingBox,
  type DistanceUnit,
  type FormattedCoordinate
} from '../types/coordinate.types'
import { isValidCoordinate, isValidLatitude, isValidLongitude } from '../utils/validation'

export class CoordinateService {
  // CoordinateService is STATELESS and renderer-agnostic.
  // It receives the renderer reference only for project/unproject operations.
  // It never subscribes to renderer events.

  /** Project a geographic coordinate to a screen pixel using the renderer. */
  project(map: MapLibreMap, coord: Coordinate): ScreenCoordinate | null {
    if (!isValidCoordinate(coord)) return null
    try {
      const point = map.project([coord.longitude, coord.latitude])
      return { x: point.x, y: point.y }
    } catch {
      return null
    }
  }

  /** Unproject a screen pixel to a geographic coordinate using the renderer. */
  unproject(map: MapLibreMap, screen: ScreenCoordinate): Coordinate | null {
    try {
      const lngLat = map.unproject([screen.x, screen.y])
      return { longitude: lngLat.lng, latitude: lngLat.lat }
    } catch {
      return null
    }
  }

  /** Calculate the geodesic distance between two coordinates using Turf. */
  calculateDistance(from: Coordinate, to: Coordinate, unit: DistanceUnit = 'kilometers'): number {
    if (!isValidCoordinate(from) || !isValidCoordinate(to)) return 0
    try {
      const fromPoint = point([from.longitude, from.latitude])
      const toPoint = point([to.longitude, to.latitude])
      return distance(fromPoint, toPoint, { units: unit })
    } catch {
      return 0
    }
  }

  /** Normalize a longitude to the range [-180, 180]. */
  normalizeLongitude(lng: number): number {
    let normalized = lng % 360
    if (normalized > 180) normalized -= 360
    if (normalized < -180) normalized += 360
    return normalized
  }

  /** Clamp a latitude to the valid Web Mercator range [-85.051129, 85.051129]. */
  clampLatitude(lat: number): number {
    return Math.max(-85.051129, Math.min(85.051129, lat))
  }

  /** Format a coordinate pair for display with direction suffix. */
  formatCoordinate(coord: Coordinate, decimals = 6): FormattedCoordinate {
    const lng = isValidLongitude(coord.longitude)
      ? coord.longitude
      : this.normalizeLongitude(coord.longitude)
    const lat = isValidLatitude(coord.latitude)
      ? coord.latitude
      : this.clampLatitude(coord.latitude)

    const lngDir = lng >= 0 ? 'E' : 'W'
    const latDir = lat >= 0 ? 'N' : 'S'

    return {
      longitude: `${Math.abs(lng).toFixed(decimals)}° ${lngDir}`,
      latitude: `${Math.abs(lat).toFixed(decimals)}° ${latDir}`,
    }
  }

  /** Extract a renderer-independent BoundingBox from the current map view. */
  extractBounds(map: MapLibreMap): BoundingBox {
    const bounds = map.getBounds()
    return {
      west: bounds.getWest(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      north: bounds.getNorth(),
    }
  }
}
