import type { NightLightsEngine } from '../../nightlights/NightLightsEngine';
import { DayNightMaskExtension } from '../extensions/DayNightMaskExtension';

export class DeckGLNightLightsBridge {
  private nightLightsEngine: NightLightsEngine;
  private readonly emissiveMapUrl = 'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_lights_2048.png';
  private maskExtension: DayNightMaskExtension;

  constructor(nightLightsEngine: NightLightsEngine) {
    this.nightLightsEngine = nightLightsEngine;
    this.maskExtension = new DayNightMaskExtension();
  }

  public getExtension(): DayNightMaskExtension {
    return this.maskExtension;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  public getUniforms(): any {
    const state = this.nightLightsEngine.getState();
    return {
      nightMaskEnabled: state.enabled,
      sunDirection: [state.sunDirectionEci.x, state.sunDirectionEci.y, state.sunDirectionEci.z],
      nightIntensity: state.intensity,
      twilightStart: state.twilightAttenuation.start,
      twilightEnd: state.twilightAttenuation.end,
      // The actual texture binding depends on Deck.gl's Texture loading mechanism.
      // Often, for extensions, we load the texture in the layer props and pass it.
      // We will provide the URL here, and DeckGLTerrainBridge or the Layer should handle it.
      nightTextureUrl: this.emissiveMapUrl
    };
  }
}
