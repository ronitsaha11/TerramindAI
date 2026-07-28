import type { OceanState, OceanOpticalProperties } from './OceanTypes';

export class OceanValidation {
  public static validateState(state: Partial<OceanState>): void {
    if (state.seaLevel !== undefined && (state.seaLevel < -11000 || state.seaLevel > 9000)) {
      throw new Error(`[OceanValidation] Sea level ${state.seaLevel} is out of realistic physical bounds.`);
    }

    if (state.opticalProperties) {
      this.validateOpticalProperties(state.opticalProperties);
    }
  }

  private static validateOpticalProperties(props: Partial<OceanOpticalProperties>): void {
    if (props.waterColor) {
      const valid = props.waterColor.every(c => c >= 0 && c <= 255);
      if (!valid) throw new Error('[OceanValidation] Water color must be in 0-255 range.');
    }
    
    if (props.specularReflectance !== undefined && (props.specularReflectance < 0 || props.specularReflectance > 1)) {
      throw new Error('[OceanValidation] Specular reflectance must be between 0 and 1.');
    }
    
    if (props.roughness !== undefined && (props.roughness < 0 || props.roughness > 1)) {
      throw new Error('[OceanValidation] Roughness must be between 0 and 1.');
    }
  }
}
