import { Deck, _GlobeView as GlobeView, type MapViewState } from '@deck.gl/core';
import type { RendererAdapter } from '../RendererAdapter';
import type { RenderingContext } from '../RenderingTypes';
import type { CameraEngine } from '../../../core/camera/CameraEngine';
import type { StreamingEngine } from '../../streaming/StreamingEngine';
import type { TerrainElevationEngine } from '../../terrain/TerrainElevationEngine';
import type { OceanSystem } from '../../ocean/OceanSystem';
import type { AtmosphereEngine } from '../../environment/AtmosphereEngine';
import type { CloudEngine } from '../../clouds/CloudEngine';
import type { NightLightsEngine } from '../../nightlights/NightLightsEngine';
import { DeckGLTerrainBridge } from '../bridges/DeckGLTerrainBridge';
import { DeckGLAtmosphereBridge } from '../bridges/DeckGLAtmosphereBridge';
import { DeckGLCloudBridge } from '../bridges/DeckGLCloudBridge';
import { DeckGLNightLightsBridge } from '../bridges/DeckGLNightLightsBridge';

export class DeckGLRendererAdapter implements RendererAdapter {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private deck: any | null = null;
  
  private container: HTMLDivElement;
  private cameraEngine: CameraEngine;
  private streamingEngine: StreamingEngine;
  private terrainEngine: TerrainElevationEngine;
  private oceanSystem: OceanSystem;
  private atmosphereEngine: AtmosphereEngine;
  private cloudEngine: CloudEngine;
  private nightLightsEngine: NightLightsEngine;
  private terrainBridge: DeckGLTerrainBridge;
  private atmosphereBridge: DeckGLAtmosphereBridge;
  private cloudBridge: DeckGLCloudBridge;
  private nightLightsBridge: DeckGLNightLightsBridge;

  constructor(
    container: HTMLDivElement,
    cameraEngine: CameraEngine,
    streamingEngine: StreamingEngine,
    terrainEngine: TerrainElevationEngine,
    oceanSystem: OceanSystem,
    atmosphereEngine: AtmosphereEngine,
    cloudEngine: CloudEngine,
    nightLightsEngine: NightLightsEngine
  ) {
    this.container = container;
    this.cameraEngine = cameraEngine;
    this.streamingEngine = streamingEngine;
    this.terrainEngine = terrainEngine;
    this.oceanSystem = oceanSystem;
    this.atmosphereEngine = atmosphereEngine;
    this.cloudEngine = cloudEngine;
    this.nightLightsEngine = nightLightsEngine;
    this.nightLightsBridge = new DeckGLNightLightsBridge(this.nightLightsEngine);
    this.terrainBridge = new DeckGLTerrainBridge(this.terrainEngine, this.oceanSystem, this.streamingEngine, this.nightLightsBridge);
    this.atmosphereBridge = new DeckGLAtmosphereBridge(this.atmosphereEngine);
    this.cloudBridge = new DeckGLCloudBridge(this.cloudEngine);
  }

  public async initialize(): Promise<boolean> {
    try {
      this.deck = new Deck({
        parent: this.container,
        initialViewState: {
          longitude: 0,
          latitude: 0,
          zoom: 0,
          minZoom: 0,
          maxZoom: 22,
          pitch: 0,
          bearing: 0
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } as any,
        views: [new GlobeView({ id: 'globe', controller: true })],
        effects: [this.atmosphereBridge.createLightingEffect()],
        onViewStateChange: ({ viewState }) => {
          const ms = viewState as MapViewState;
          // Route user interaction directly back to the authoritative domain
          this.cameraEngine.jumpTo({
            longitude: ms.longitude,
            latitude: ms.latitude,
            pitch: ms.pitch,
            bearing: ms.bearing,
            altitude: this.zoomToAltitude(ms.zoom)
          });
        },
        layers: []
        // parameters: {
        //   clearColor: [0, 0, 0, 1] // Deep space black background
        // }
      });
      return true;
    } catch (e) {
      console.error('[DeckGLRendererAdapter] Failed to initialize Deck:', e);
      return false;
    }
  }

  public applyContext(context: Readonly<RenderingContext>): void {
    if (!this.deck) return;

    const zoom = this.altitudeToZoom(context.camera.altitude);

    this.deck.setProps({
      viewState: {
        longitude: context.camera.longitude,
        latitude: context.camera.latitude,
        zoom,
        pitch: context.camera.pitch,
        bearing: context.camera.bearing
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
      layers: [
        this.terrainBridge.createTerrainLayer(),
        this.cloudBridge.createCloudLayer()
      ].filter(Boolean)
    });
  }

  public destroy(): void {
    if (this.deck) {
      this.deck.finalize();
      this.deck = null;
    }
  }

  /**
   * Translates the pure domain altitude (meters) to Deck.gl's screen-space zoom level.
   * Approximation: zoom 0 is ~35,000,000 meters above surface.
   */
  private altitudeToZoom(altitude: number): number {
    if (altitude <= 0) return 22; // Max zoom safeguard
    return Math.log2(35000000 / altitude);
  }

  /**
   * Translates Deck.gl's screen-space zoom level back to physical altitude (meters).
   */
  private zoomToAltitude(zoom: number): number {
    return 35000000 / Math.pow(2, zoom);
  }
}
