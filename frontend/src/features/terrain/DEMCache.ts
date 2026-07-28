import type { CachePolicy, CacheStatistics, TileIndex } from '../streaming/StreamingTypes';
import { DEFAULT_CACHE_POLICY } from '../streaming/StreamingConfig';
import type { ElevationMetadata } from './DEMTypes';

export class DEMCache {
  private policy: CachePolicy;
  private metadata = new Map<string, ElevationMetadata>();
  
  private stats: CacheStatistics = {
    tilesInCache: 0,
    memoryUsedBytes: 0,
    evictionCount: 0
  };

  constructor(policy: CachePolicy = DEFAULT_CACHE_POLICY) {
    this.policy = policy;
  }

  public registerTile(index: TileIndex, meta: ElevationMetadata): void {
    const key = this.getTileKey(index);
    if (!this.metadata.has(key)) {
      this.metadata.set(key, meta);
      this.stats.tilesInCache++;
      this.enforcePolicy();
    }
  }

  public evictTile(index: TileIndex): void {
    const key = this.getTileKey(index);
    if (this.metadata.delete(key)) {
      this.stats.tilesInCache--;
    }
  }

  private enforcePolicy(): void {
    while (this.stats.tilesInCache > this.policy.maxTiles) {
      const firstKey = this.metadata.keys().next().value;
      if (firstKey) {
        this.evictTile(this.parseTileKey(firstKey));
        this.stats.evictionCount++;
      } else {
        break;
      }
    }
  }

  private getTileKey(index: TileIndex): string {
    return `${index.z}/${index.x}/${index.y}`;
  }

  private parseTileKey(key: string): TileIndex {
    const [z, x, y] = key.split('/').map(Number);
    return { z, x, y };
  }
}
