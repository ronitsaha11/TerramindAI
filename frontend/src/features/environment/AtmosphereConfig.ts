export const ATMOSPHERE_CONSTANTS = {
  // Typical Earth values in meters
  planetRadius: 6371000,
  atmosphereRadius: 6471000,

  // Standard scattering parameters
  rayleighScaleHeight: 8000.0,
  mieScaleHeight: 1200.0,

  // Wavelengths corresponding roughly to R, G, B at sea level
  rayleighScattering: { x: 5.8e-6, y: 1.35e-5, z: 3.31e-5 },
  mieScattering: 3.9e-6
};
