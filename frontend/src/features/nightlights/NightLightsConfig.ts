export const DEFAULT_NIGHT_LIGHTS_CONFIG = {
  enabled: true,
  intensity: 1.0,
  twilightAttenuation: {
    start: 0.1, // sun elevation dot product where lights start fading in
    end: -0.1   // sun elevation dot product where lights are fully on
  }
};
