import { TileLayer } from '@deck.gl/geo-layers';
import { BitmapLayer } from '@deck.gl/layers';
import type { StreamingEngine } from '../../streaming/StreamingEngine';

export class DeckGLTileBridge {
  private streamingEngine: StreamingEngine;

  constructor(streamingEngine: StreamingEngine) {
    this.streamingEngine = streamingEngine;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  public createBaseImageryLayer(): any {
    const policyState = this.streamingEngine.getPolicyState();

    return new TileLayer({
      id: 'base-imagery',
      // Using CartoDB light map as public development tile source
      data: 'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
      
      minZoom: policyState.minZoom,
      maxZoom: policyState.maxZoom,
      tileSize: 256,
      
      // Deck.gl built-in refinement controls based on domain policy
      extent: [-180, -90, 180, 90],
      
      // Progressive refinement: keeps parent tiles while children are loading
      refinementStrategy: 'best-available',
      
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onTileLoad: (tile: any) => {
        // Report loaded tile back to domain StreamingEngine's Cache
        this.streamingEngine.getCache().registerTile({
          index: { x: tile.index.x, y: tile.index.y, z: tile.index.z },
          url: tile.url,
          // Rough estimation of image size if true size isn't exposed
          sizeBytes: 256 * 256 * 4
        });
        
        this.streamingEngine.events.emitTileLoaded({
          index: { x: tile.index.x, y: tile.index.y, z: tile.index.z },
          url: tile.url
        });
      },

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onTileUnload: (tile: any) => {
        // Remove from domain cache representation
        this.streamingEngine.getCache().evictTile({
          x: tile.index.x,
          y: tile.index.y,
          z: tile.index.z
        });
      },

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      renderSubLayers: (props: any) => {
        const {
          bbox: { west, south, east, north }
        } = props.tile;

        return new BitmapLayer(props, {
          data: undefined,
          image: props.data,
          bounds: [west, south, east, north]
        });
      }
    });
  }
}
