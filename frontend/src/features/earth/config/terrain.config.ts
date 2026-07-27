import { type RasterDEMSourceSpecification } from 'maplibre-gl'

export const TERRAIN_CONFIG = {
  SOURCE_ID: 'terramind-dem',
  SOURCE: {
    type: 'raster-dem',
    url: 'https://demotiles.maplibre.org/terrain-tiles/tiles.json',
    tileSize: 256,
  } as RasterDEMSourceSpecification,
  EXAGGERATION: 1.5,
}
