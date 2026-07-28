import type { TwilightAttenuation } from './NightLightsTypes';
import type { Vector3 } from '../environment/AtmosphereState';

export interface NightLightsState {
  enabled: boolean;
  intensity: number;
  twilightAttenuation: TwilightAttenuation;
  sunDirectionEci: Vector3;
}
