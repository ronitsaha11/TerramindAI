import type { CachePolicy } from './StreamingTypes';

export const DEFAULT_CACHE_POLICY: CachePolicy = {
  // e.g. 512 MB memory limit
  maxMemoryBytes: 512 * 1024 * 1024,
  // Reasonable max tile count for standard resolutions
  maxTiles: 1000
};

export const DEFAULT_STREAMING_POLICY = {
  minZoom: 0,
  maxZoom: 19,
  retainParents: true
};
