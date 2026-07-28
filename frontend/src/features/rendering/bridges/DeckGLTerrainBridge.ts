import { TerrainLayer } from '@deck.gl/geo-layers';
import type { TerrainElevationEngine } from '../../terrain/TerrainElevationEngine';
import type { OceanSystem } from '../../ocean/OceanSystem';
import type { StreamingEngine } from '../../streaming/StreamingEngine';

export class DeckGLTerrainBridge {
  private terrainEngine: TerrainElevationEngine;
  private oceanSystem: OceanSystem;
  private streamingEngine: StreamingEngine;

  constructor(
    terrainEngine: TerrainElevationEngine,
    oceanSystem: OceanSystem,
    streamingEngine: StreamingEngine
  ) {
    this.terrainEngine = terrainEngine;
    this.oceanSystem = oceanSystem;
    this.streamingEngine = streamingEngine;
  }

  public getOceanSystem(): OceanSystem {
    return this.oceanSystem;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  public createTerrainLayer(): any {
    const terrainPolicy = this.terrainEngine.getParameters();
    const provider = this.terrainEngine.getProvider();
    const providerConfig = provider.getConfig();
    const streamingPolicy = this.streamingEngine.getPolicyState();
    // In Deck.gl, terrain supports color parameters, we map ocean state here if needed
    // const oceanState = this.oceanSystem.getState();

    return new TerrainLayer({
      id: 'terrain-layer',
      
      // Elevation Data
      elevationData: providerConfig.url,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      elevationDecoder: provider.getElevationDecoder() as any,
      
      // Base Imagery
      texture: 'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
      
      // Streaming constraints combined from both engines
      minZoom: Math.max(streamingPolicy.minZoom, providerConfig.minZoom),
      maxZoom: Math.min(streamingPolicy.maxZoom, providerConfig.maxZoom),
      
      // Domain Terrain parameters
      elevationDataExaggeration: terrainPolicy.exaggeration,
      meshMaxError: terrainPolicy.meshMaxError,
      
      // Extent
      extent: [-180, -90, 180, 90],
      refinementStrategy: 'best-available',

      // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars
      onViewportLoad: (_tiles: any[]) => {
        // Here we could report back loaded chunks to the Terrain Cache
        // or let Deck.gl manage it natively and just track stats
      }
    });
  }
}
