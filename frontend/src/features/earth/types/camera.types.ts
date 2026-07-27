/** Full camera position state — the canonical model throughout TerraMind. */
export interface CameraPosition {
  longitude: number
  latitude: number
  zoom: number
  pitch: number
  bearing: number
}

/** Geographic bounding box used for fitBounds operations. */
export interface CameraBounds {
  west: number
  south: number
  east: number
  north: number
}

/** Options for flyTo camera animation. */
export interface FlyToOptions {
  center: [number, number]
  zoom?: number
  pitch?: number
  bearing?: number
  duration?: number
  curve?: number
}

/** Options for jumpTo — instant camera transition. */
export interface JumpToOptions {
  center?: [number, number]
  zoom?: number
  pitch?: number
  bearing?: number
}

/** Options for fitBounds. */
export interface FitBoundsOptions {
  padding?: number | { top: number; bottom: number; left: number; right: number }
  maxZoom?: number
  duration?: number
}
