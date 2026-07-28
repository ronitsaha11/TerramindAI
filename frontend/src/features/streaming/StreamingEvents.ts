import type { TileMetadata, CacheStatistics } from './StreamingTypes';

type EventCallback<T> = (data: T) => void;

export class StreamingEvents {
  private onTileLoadedHandlers: Set<EventCallback<TileMetadata>> = new Set();
  private onTileEvictedHandlers: Set<EventCallback<TileMetadata>> = new Set();
  private onCacheUpdatedHandlers: Set<EventCallback<CacheStatistics>> = new Set();

  public onTileLoaded(handler: EventCallback<TileMetadata>): () => void {
    this.onTileLoadedHandlers.add(handler);
    return () => this.onTileLoadedHandlers.delete(handler);
  }

  public emitTileLoaded(metadata: TileMetadata): void {
    this.onTileLoadedHandlers.forEach(h => h(metadata));
  }

  public onTileEvicted(handler: EventCallback<TileMetadata>): () => void {
    this.onTileEvictedHandlers.add(handler);
    return () => this.onTileEvictedHandlers.delete(handler);
  }

  public emitTileEvicted(metadata: TileMetadata): void {
    this.onTileEvictedHandlers.forEach(h => h(metadata));
  }

  public onCacheUpdated(handler: EventCallback<CacheStatistics>): () => void {
    this.onCacheUpdatedHandlers.add(handler);
    return () => this.onCacheUpdatedHandlers.delete(handler);
  }

  public emitCacheUpdated(stats: CacheStatistics): void {
    this.onCacheUpdatedHandlers.forEach(h => h(stats));
  }
}
