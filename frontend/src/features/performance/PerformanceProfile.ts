export interface PerformanceProfile {
  meshQuality: number;       // e.g. 1 (low) to 4 (ultra)
  useDevicePixels: boolean;  // higher res scaling
  cloudQuality: number;      // e.g. 0 (disabled) to 3 (high)
  nightLightsEnabled: boolean;
  atmosphereQuality: number; // e.g. 1 to 3
}

export const LOW_PROFILE: PerformanceProfile = {
  meshQuality: 1,
  useDevicePixels: false,
  cloudQuality: 0,
  nightLightsEnabled: false,
  atmosphereQuality: 1
};

export const MEDIUM_PROFILE: PerformanceProfile = {
  meshQuality: 2,
  useDevicePixels: false,
  cloudQuality: 1,
  nightLightsEnabled: true,
  atmosphereQuality: 2
};

export const HIGH_PROFILE: PerformanceProfile = {
  meshQuality: 3,
  useDevicePixels: true,
  cloudQuality: 2,
  nightLightsEnabled: true,
  atmosphereQuality: 3
};

export const ULTRA_PROFILE: PerformanceProfile = {
  meshQuality: 4,
  useDevicePixels: true,
  cloudQuality: 3,
  nightLightsEnabled: true,
  atmosphereQuality: 3
};
