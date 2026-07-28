/**
 * Represents the supported dataset types in TerraMind AI.
 * Designed to be extensible for future formats.
 */
export type DatasetType =
  | 'geojson'
  | 'vector-tile'
  | 'pmtiles'
  | 'geotiff'
  | 'kml'
  | 'shapefile'
  | 'csv'
  | 'wms'
  | 'wmts'
  | 'custom'
  | (string & {}); // Allows future custom string values while preserving autocomplete
