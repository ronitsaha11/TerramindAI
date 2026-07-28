export interface OceanOpticalProperties {
  waterColor: [number, number, number];
  specularReflectance: number;
  roughness: number;
}

export interface OceanState {
  enabled: boolean;
  seaLevel: number;
  opticalProperties: OceanOpticalProperties;
}
