import type { OceanState } from './OceanTypes';

export const DEFAULT_OCEAN_STATE: OceanState = {
  enabled: true,
  seaLevel: 0,
  opticalProperties: {
    // Standard deep ocean blue
    waterColor: [10, 30, 60],
    specularReflectance: 0.5,
    roughness: 0.2
  }
};
