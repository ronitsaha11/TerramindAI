import { DEFAULT_CACHE_POLICY } from './StreamingConfig';
import type { CachePolicy, CacheStatistics, TileIndex, TileMetadata } from './StreamingTypes';

export class StreamingCache {
  private policy: CachePolicy;
  
  // LRU map storing tile metadata
  private tiles = new Map<string, TileMetadata>();
  
  private stats: CacheStatistics = {
    tilesInCache: 0,
    memoryUsedBytes: 0,
    evictionCount: 0
  };

  constructor(policy: CachePolicy = DEFAULT_CACHE_POLICY) {
    this.policy = policy;
  }

  public registerTile(tile: TileMetadata): void {
    const key = this.getTileKey(tile.index);
    
    if (this.tiles.has(key)) {
      // Move to end for LRU
      this.tiles.delete(key);
      this.tiles.set(key, tile);
      return;
    }

    this.tiles.set(key, tile);
    this.stats.tilesInCache++;
    this.stats.memoryUsedBytes += (tile.sizeBytes || 0);

    this.enforcePolicy();
  }

  public evictTile(index: TileIndex): void {
    const key = this.getTileKey(index);
    const tile = this.tiles.get(key);
    if (tile) {
      this.stats.tilesInCache--;
      this.stats.memoryUsedBytes -= (tile.sizeBytes || 0);
      this.tiles.delete(key);
    }
  }

  private enforcePolicy(): void {
    // Basic LRU eviction
    while (this.stats.tilesInCache > this.policy.maxTiles || this.stats.memoryUsedBytes > this.policy.maxMemoryBytes) {
      const firstKey = this.tiles.keys().next().value;
      if (firstKey) {
        this.evictTile(this.parseTileKey(firstKey));
        this.stats.evictionCount++;
      } else {
        break;
      }
    }
  }

  public getStats(): Readonly<CacheStatistics> {
    return this.stats;
  }

  private getTileKey(index: TileIndex): string {
    return `${index.z}/${index.x}/${index.y}`;
  }

  private parseTileKey(key: string): TileIndex {
    const [z, x, y] = key.split('/').map(Number);
    return { z, x, y };
  }
}
