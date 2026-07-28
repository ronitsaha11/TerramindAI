import { PointCloudLayer, IconLayer } from '@deck.gl/layers';
import type { SpaceEngine } from '../../space/SpaceEngine';

export class DeckGLSpaceBridge {
  private spaceEngine: SpaceEngine;

  constructor(spaceEngine: SpaceEngine) {
    this.spaceEngine = spaceEngine;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  public createLayers(): any[] {
    const state = this.spaceEngine.getState();
    const layers = [];

    // Background color is usually set on the Deck.gl view or canvas directly
    // In our architecture, the RendererAdapter might consume backgroundColor to clear the canvas.
    
    if (state.starConfig.visibility) {
      // In a real implementation, we would generate a buffer of random star coordinates (RA/Dec mapped to x,y,z on a far sphere)
      // For Phase 11.5.B11, we stub the layer to prove architectural integration.
      layers.push(new PointCloudLayer({
        id: 'star-field',
        data: [{ position: [0, 0, -1000000] }], // stub data
        getPosition: (d: { position: [number, number, number] }) => d.position,
        getNormal: [0, 1, 0],
        getColor: [255, 255, 255, 255 * state.starConfig.intensity],
        pointSize: 2
        // Rotation would be applied via coordinate system or a model matrix using state.celestialRotationDegrees
      }));
    }

    // Sun Icon
    // Mapping sun direction to a far coordinate for the sun sprite
    const sunDist = 149600000000; // Roughly 1 AU in meters
    const sx = state.sunDirectionEci.x * sunDist;
    const sy = state.sunDirectionEci.y * sunDist;
    const sz = state.sunDirectionEci.z * sunDist;

    layers.push(new IconLayer({
      id: 'sun-sprite',
      data: [{ position: [sx, sy, sz], icon: 'sun' }],
      getPosition: (d: { position: [number, number, number] }) => d.position,
      getIcon: () => ({
        url: 'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/lensflare/lensflare0.png',
        width: 512,
        height: 512,
        anchorY: 256
      }),
      getSize: 100,
      sizeUnits: 'pixels'
    }));

    // Moon Icon
    // Position provided directly from ephemeris mapped state
    const mx = state.moonPositionEci.x;
    const my = state.moonPositionEci.y;
    const mz = state.moonPositionEci.z;

    layers.push(new IconLayer({
      id: 'moon-sprite',
      data: [{ position: [mx, my, mz], icon: 'moon' }],
      getPosition: (d: { position: [number, number, number] }) => d.position,
      getIcon: () => ({
        url: 'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/moon_1024.jpg',
        width: 1024,
        height: 1024,
        anchorY: 512
      }),
      getSize: 50,
      sizeUnits: 'pixels'
    }));

    return layers;
  }
}
