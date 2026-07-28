import { SolidPolygonLayer } from '@deck.gl/layers';
import type { RenderingContext } from '../RenderingTypes';

export class GlobeLayerFactory {
  /**
   * Creates a minimal layer representing the Earth sphere to validate the rendering pipeline.
   * This is a placeholder for future terrain, imagery, and atmosphere systems.
   */
  public static createGlobeLayers(context: RenderingContext): import('@deck.gl/core').Layer[] {
    // A simple polygon covering the entire coordinate space.
    // In GlobeView, Deck.gl wraps this around the sphere.
    const earthPolygon = [
      [-180, -90],
      [180, -90],
      [180, 90],
      [-180, 90],
      [-180, -90]
    ];

    // We can use sunDirectionEcef here for lighting calculations later.
    // const { x, y, z } = context.lighting.sunDirectionEcef;

    const layer = new SolidPolygonLayer({
      id: 'base-globe',
      data: [{ polygon: earthPolygon }],
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      getPolygon: (d: any) => d.polygon,
      getFillColor: [10, 20, 40], // Dark ocean/space blue
      extruded: false,
      material: {
        ambient: 0.1,
        diffuse: context.lighting.sunIntensity,
        shininess: 32,
        specularColor: [60, 64, 70]
      }
    });

    return [layer];
  }
}
