export interface TileIndex {
  x: number;
  y: number;
  z: number;
}

export interface TileMetadata {
  index: TileIndex;
  url: string;
  sizeBytes?: number;
  boundingBox?: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
}

export interface CachePolicy {
  maxMemoryBytes: number;
  maxTiles: number;
}

export interface StreamingPolicyState {
  minZoom: number;
  maxZoom: number;
  // Dynamic threshold for tile subdivision based on altitude
  currentLOD: number;
  // Whether parent tiles should be retained while children load
  retainParents: boolean;
}

export interface CacheStatistics {
  tilesInCache: number;
  memoryUsedBytes: number;
  evictionCount: number;
}
