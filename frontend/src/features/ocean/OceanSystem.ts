import type { OceanState, OceanOpticalProperties } from './OceanTypes';
import { DEFAULT_OCEAN_STATE } from './OceanConfig';
import { OceanValidation } from './OceanValidation';

export class OceanSystem {
  private state: OceanState;

  constructor(initialState?: Partial<OceanState>) {
    if (initialState) OceanValidation.validateState(initialState);
    this.state = { ...DEFAULT_OCEAN_STATE, ...initialState };
  }

  public getState(): Readonly<OceanState> {
    return this.state;
  }

  public setEnabled(enabled: boolean): void {
    this.state.enabled = enabled;
  }

  public setSeaLevel(level: number): void {
    OceanValidation.validateState({ seaLevel: level });
    this.state.seaLevel = level;
  }

  public setOpticalProperties(props: Partial<OceanOpticalProperties>): void {
    OceanValidation.validateState({ opticalProperties: { ...this.state.opticalProperties, ...props } });
    this.state.opticalProperties = { ...this.state.opticalProperties, ...props };
  }
}
