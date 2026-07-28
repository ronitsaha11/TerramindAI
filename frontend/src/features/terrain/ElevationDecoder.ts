export const MAPZEN_ELEVATION_DECODER = {
  rScaler: 256,
  gScaler: 1,
  bScaler: 1 / 256,
  offset: -32768
};

// Mapbox RGB elevation decoding is slightly different:
// elevation = -10000 + ((R * 256 * 256 + G * 256 + B) * 0.1)
export const MAPBOX_ELEVATION_DECODER = {
  rScaler: 6553.6,
  gScaler: 25.6,
  bScaler: 0.1,
  offset: -10000
};
