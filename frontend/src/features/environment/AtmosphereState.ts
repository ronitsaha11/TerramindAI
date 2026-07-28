export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface AtmosphereState {
  // Physical radii
  planetRadius: number; // e.g. 6371000 meters
  atmosphereRadius: number; // e.g. 6471000 meters

  // Scattering coefficients
  rayleighScattering: Vector3;
  mieScattering: number;

  // Scale heights
  rayleighScaleHeight: number;
  mieScaleHeight: number;

  // Ephemeris integration
  sunDirectionEci: Vector3;

  // Generated Sky state (consumed directly by simpler renderers)
  zenithColor: [number, number, number];
  horizonColor: [number, number, number];
  ambientIntensity: number;
  twilightFactor: number;
}
