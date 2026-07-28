export interface DEMProviderConfig {
  id: string;
  url: string;
  maxZoom: number;
  minZoom: number;
  attribution?: string;
}

export interface ElevationMetadata {
  minElevation: number;
  maxElevation: number;
  meanElevation: number;
}

export interface TerrainParameters {
  exaggeration: number;
  meshMaxError: number;
}
