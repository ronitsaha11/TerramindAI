import { create } from 'zustand'
import { type Coordinate, type ScreenCoordinate } from '../types/coordinate.types'

type CursorState = {
  longitude: number | null
  latitude: number | null
  screenX: number
  screenY: number
  setCursor: (coord: Coordinate & ScreenCoordinate) => void
  clearCursor: () => void
}

export const useCursorStore = create<CursorState>((set) => ({
  longitude: null,
  latitude: null,
  screenX: 0,
  screenY: 0,
  setCursor: ({ longitude, latitude, x, y }) =>
    set({ longitude, latitude, screenX: x, screenY: y }),
  clearCursor: () =>
    set({ longitude: null, latitude: null, screenX: 0, screenY: 0 }),
}))
