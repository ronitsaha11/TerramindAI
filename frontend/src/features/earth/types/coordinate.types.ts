/** A geographic world coordinate [longitude, latitude]. */
export interface Coordinate {
  longitude: number
  latitude: number
}

/** A point on the screen in pixels. */
export interface ScreenCoordinate {
  x: number
  y: number
}

/** An axis-aligned geographic bounding box. */
export interface BoundingBox {
  west: number
  south: number
  east: number
  north: number
}

/** Width and height of a viewport in pixels. */
export interface ViewportSize {
  width: number
  height: number
}

/** Supported units for distance measurements. */
export type DistanceUnit = 'kilometers' | 'miles' | 'meters' | 'degrees'

/** A formatted coordinate string with optional direction suffix. */
export interface FormattedCoordinate {
  longitude: string
  latitude: string
}
