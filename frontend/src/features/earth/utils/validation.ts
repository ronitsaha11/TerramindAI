import { type Coordinate } from '../types/coordinate.types'

/** Clamp a latitude value to the valid WGS-84 range [-85.051129, 85.051129]. */
export function isValidLatitude(lat: number): boolean {
  return Number.isFinite(lat) && lat >= -85.051129 && lat <= 85.051129
}

/** Check that a longitude is within the valid range [-180, 180]. */
export function isValidLongitude(lng: number): boolean {
  return Number.isFinite(lng) && lng >= -180 && lng <= 180
}

/** Check that a coordinate object has valid longitude and latitude values. */
export function isValidCoordinate(coord: Coordinate): boolean {
  return isValidLongitude(coord.longitude) && isValidLatitude(coord.latitude)
}

/** Check that a zoom level is within the typical MapLibre range [0, 24]. */
export function isValidZoom(zoom: number): boolean {
  return Number.isFinite(zoom) && zoom >= 0 && zoom <= 24
}
