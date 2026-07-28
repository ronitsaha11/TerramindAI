import { TerrainLayer } from '@deck.gl/geo-layers';
import type { TerrainElevationEngine } from '../../terrain/TerrainElevationEngine';
import type { OceanSystem } from '../../ocean/OceanSystem';
import type { StreamingEngine } from '../../streaming/StreamingEngine';
import type { DeckGLNightLightsBridge } from './DeckGLNightLightsBridge';

export class DeckGLTerrainBridge {
  private terrainEngine: TerrainElevationEngine;
  private oceanSystem: OceanSystem;
  private streamingEngine: StreamingEngine;
  private nightLightsBridge?: DeckGLNightLightsBridge;

  constructor(
    terrainEngine: TerrainElevationEngine,
    oceanSystem: OceanSystem,
    streamingEngine: StreamingEngine,
    nightLightsBridge?: DeckGLNightLightsBridge
  ) {
    this.terrainEngine = terrainEngine;
    this.oceanSystem = oceanSystem;
    this.streamingEngine = streamingEngine;
    this.nightLightsBridge = nightLightsBridge;
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
    
    const extensions = [];
    const materialConfig = {
      ambient: 0.1,
      diffuse: 0.9,
      shininess: 0,
      specularColor: [0, 0, 0] as [number, number, number]
    };
    
    // We only need to configure the uniform if we're rendering night lights
    // but the actual uniforms object might need to be passed in differently depending on the DeckGL version.
    // Usually, extensions inject uniforms automatically if provided via `updateState` or top-level props.
    // DeckGL automatically merges extension uniforms from the layer's props or the extension's getUniforms.
    let nightLightProps = {};

    if (this.nightLightsBridge) {
      extensions.push(this.nightLightsBridge.getExtension());
      nightLightProps = this.nightLightsBridge.getUniforms();
    }

    return new TerrainLayer({
      id: 'terrain-layer',
      ...nightLightProps,
      
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
      },
      
      wireframe: false,
      material: materialConfig,
      extensions: extensions
    });
  }
}
