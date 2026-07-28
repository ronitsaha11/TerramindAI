import { NightLightsEvents } from './NightLightsEvents';
import { NightLightsValidation } from './NightLightsValidation';
import { DEFAULT_NIGHT_LIGHTS_CONFIG } from './NightLightsConfig';
import type { NightLightsState } from './NightLightsState';
import type { AtmosphereEngine } from '../environment/AtmosphereEngine';

export class NightLightsEngine {
  public readonly events = new NightLightsEvents();
  
  private atmosphereEngine: AtmosphereEngine;
  private state: NightLightsState;
  
  private unsubAtmosphere: (() => void) | null = null;

  constructor(atmosphereEngine: AtmosphereEngine) {
    this.atmosphereEngine = atmosphereEngine;

    // Initial state based on current atmosphere
    const atmosphereState = this.atmosphereEngine.getState();
    this.state = {
      enabled: DEFAULT_NIGHT_LIGHTS_CONFIG.enabled,
      intensity: DEFAULT_NIGHT_LIGHTS_CONFIG.intensity,
      twilightAttenuation: { ...DEFAULT_NIGHT_LIGHTS_CONFIG.twilightAttenuation },
      sunDirectionEci: { ...atmosphereState.sunDirectionEci }
    };
  }

  public initialize(): void {
    // Subscribe to sun direction changes from Atmosphere
    this.unsubAtmosphere = this.atmosphereEngine.events.onStateUpdated((atmState) => {
      this.updateSunDirection(atmState.sunDirectionEci);
    });

    this.events.emitStateUpdated(this.state);
  }

  public setEnabled(enabled: boolean): void {
    this.state = { ...this.state, enabled };
    this.events.emitStateUpdated(this.state);
  }

  public setIntensity(intensity: number): void {
    NightLightsValidation.validateIntensity(intensity);
    this.state = { ...this.state, intensity };
    this.events.emitStateUpdated(this.state);
  }

  private updateSunDirection(sunDirectionEci: { x: number; y: number; z: number }): void {
    // We only mutate state and notify if the direction changes meaningfully.
    // In a full implementation we might diff to prevent spamming, but React/Deck 
    // handles object reference diffing internally.
    this.state = {
      ...this.state,
      sunDirectionEci: { ...sunDirectionEci }
    };
    this.events.emitStateUpdated(this.state);
  }

  public getState(): Readonly<NightLightsState> {
    return this.state;
  }

  public destroy(): void {
    if (this.unsubAtmosphere) {
      this.unsubAtmosphere();
      this.unsubAtmosphere = null;
    }
  }
}
