import { LayerExtension } from '@deck.gl/core';

// This implements a standard WebGL extension injected into Deck.gl's layer fragment shader
// It applies a custom mask for night lighting depending on sun direction.
export class DayNightMaskExtension extends LayerExtension {
  getShaders() {
    return {
      inject: {
        // We inject into the fragment shader at the point where color has been calculated
        // DeckGL often provides `vec4 geometry.normal` or `vec3 normals_common`
        // However, standard GlobeView sets up lighting. 
        // For our emissive mapping, we assume a uniform `nightTexture` is bound (via bridge).
        'fs:#decl': `
          uniform vec3 sunDirection;
          uniform float nightIntensity;
          uniform float twilightStart;
          uniform float twilightEnd;
          uniform sampler2D nightTexture;
          uniform bool nightMaskEnabled;
        `,
        'fs:#main-end': `
          if (nightMaskEnabled) {
            // Get the normal of the sphere (approximate for globe)
            // Deck.gl's GlobeView sets up geometry.normal in world space.
            vec3 normal = normalize(geometry.normal);
            
            // Calculate the dot product with the sun direction
            float sunDot = dot(normal, normalize(sunDirection));
            
            // Calculate the twilight fade factor using smoothstep
            // If sunDot > twilightStart (day), factor = 0
            // If sunDot < twilightEnd (night), factor = 1
            float nightFactor = smoothstep(twilightStart, twilightEnd, sunDot);
            
            // Sample the emissive map
            // Assuming geometry.uv is available. If using TerrainLayer, uv is standard.
            vec4 nightColor = texture2D(nightTexture, geometry.uv);
            
            // Additive blending of the night lights onto the base color
            // DeckGL's final color is gl_FragColor.
            vec3 emissive = nightColor.rgb * nightIntensity * nightFactor;
            
            gl_FragColor.rgb = gl_FragColor.rgb + emissive;
          }
        `
      }
    };
  }
}
