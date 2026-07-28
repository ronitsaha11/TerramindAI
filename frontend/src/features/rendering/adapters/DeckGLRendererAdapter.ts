import { Deck, _GlobeView as GlobeView, type MapViewState } from '@deck.gl/core';
import type { RendererAdapter } from '../RendererAdapter';
import type { RenderingContext } from '../RenderingTypes';
import { GlobeLayerFactory } from '../layers/GlobeLayerFactory';
import type { CameraEngine } from '../../../core/camera/CameraEngine';

export class DeckGLRendererAdapter implements RendererAdapter {
  private deck: any | null = null;
  
  private container: HTMLDivElement;
  private cameraEngine: CameraEngine;

  constructor(
    container: HTMLDivElement,
    cameraEngine: CameraEngine
  ) {
    this.container = container;
    this.cameraEngine = cameraEngine;
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
        } as any,
        views: [new GlobeView({ id: 'globe', controller: true })],
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
      } as any,
      layers: GlobeLayerFactory.createGlobeLayers(context)
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
