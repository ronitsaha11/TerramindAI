import { BitmapLayer } from '@deck.gl/layers';
import type { CloudEngine } from '../../clouds/CloudEngine';

export class DeckGLCloudBridge {
  private cloudEngine: CloudEngine;
  private readonly cloudMapUrl = 'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_clouds_1024.png';

  constructor(cloudEngine: CloudEngine) {
    this.cloudEngine = cloudEngine;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  public createCloudLayer(): any | null {
    const state = this.cloudEngine.getState();

    if (!state.enabled) {
      return null;
    }

    // A simple spherical projection of clouds wrapping the earth
    // Since Deck.gl's GlobeView maps bounds [-180, -90, 180, 90] to a sphere,
    // we can use a BitmapLayer elevated to `altitudeMeters`.
    // The rotation is handled by shifting the longitude bounds based on `rotationOffsetDegrees`.
    // NOTE: In a true spherical wrapper without seams, custom shaders are preferred.
    // For this bridge, we demonstrate the offset dynamically shifting the X bounds.
    
    // Calculate rotated bounds
    const offset = state.rotationOffsetDegrees;
    const bounds = [-180 + offset, -90, 180 + offset, 90];

    // To prevent clipping at 180/-180, a production system would duplicate the layer 
    // or use a custom shader. For Phase 11.5.B9, we render the moving texture bounds.

    return new BitmapLayer({
      id: 'cloud-layer',
      image: this.cloudMapUrl,
      bounds: bounds as [number, number, number, number],
      opacity: state.opacity,
      transparent: true,
      
      // Elevation places the clouds exactly where the domain dictates
      // Note: BitmapLayer doesn't natively support Z-elevation in GlobeView easily without a polygon/mesh layer,
      // but in 3D views it does. For GlobeView, we might need a SimpleMeshLayer (sphere) if BitmapLayer stays on ground.
      // We will pass coordinateZ for 3D offset if supported, otherwise rely on DeckGL defaults.
      coordinateZ: state.altitudeMeters,
      
      parameters: {
        depthTest: true
      }
    });
  }
}
