export interface PlanetConfig {
  /** 
   * If true, enables strict boundary validation on coordinates.
   * If false, invalid coordinates may gracefully clamp or wrap.
   */
  strictValidation: boolean;
}

export const DEFAULT_PLANET_CONFIG: PlanetConfig = {
  strictValidation: true,
};
