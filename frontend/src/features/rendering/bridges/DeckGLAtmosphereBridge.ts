import { LightingEffect, AmbientLight, _SunLight as SunLight } from '@deck.gl/core';
import type { AtmosphereEngine } from '../../environment/AtmosphereEngine';

export class DeckGLAtmosphereBridge {
  private atmosphereEngine: AtmosphereEngine;

  constructor(atmosphereEngine: AtmosphereEngine) {
    this.atmosphereEngine = atmosphereEngine;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  public createLightingEffect(): any {
    const state = this.atmosphereEngine.getState();

    // Map the simplified sky state into Deck.gl's AmbientLight
    const ambientLight = new AmbientLight({
      color: state.zenithColor,
      intensity: state.ambientIntensity
    });

    // Extract the directional sun vector from the ephemeris simulation
    // DeckGL _SunLight computes its own projection based on timestamp/timezone historically,
    // but we can provide raw directional intensity in advanced custom effects later.
    // For now, we will construct a default SunLight object if timestamp is available,
    // or alternatively, we can use a basic DirectionalLight mapped to our ECI vector.
    // Given Deck's standard model, we use SunLight which aligns with GlobeView naturally.
    const sunLight = new SunLight({
      timestamp: Date.now(), // In a fully integrated ephemeris, pass the simulation time here
      color: [255, 255, 255],
      intensity: 1.0 // Base intensity before atmospheric attenuation
    });

    return new LightingEffect({ ambientLight, sunLight });
  }
}
