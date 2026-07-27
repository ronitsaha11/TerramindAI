import { point } from '@turf/helpers'
import { bbox } from '@turf/bbox'
import { center } from '@turf/center'
import { type BoundingBox, type Coordinate } from '../types/coordinate.types'

/** Create a GeoJSON point from a Coordinate. */
export function coordinateToPoint(coord: Coordinate) {
  return point([coord.longitude, coord.latitude])
}

/** Compute the centroid of a set of coordinates. */
export function centroid(coords: Coordinate[]): Coordinate {
  const features = coords.map(c => coordinateToPoint(c))
  const collection = { type: 'FeatureCollection' as const, features }
  const c = center(collection)
  const [lng, lat] = c.geometry.coordinates
  return { longitude: lng, latitude: lat }
}

/** Compute the bounding box of a set of coordinates. */
export function coordinateBBox(coords: Coordinate[]): BoundingBox {
  const features = coords.map(c => coordinateToPoint(c))
  const collection = { type: 'FeatureCollection' as const, features }
  const [west, south, east, north] = bbox(collection)
  return { west, south, east, north }
}
