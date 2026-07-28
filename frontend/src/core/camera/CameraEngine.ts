import type { CameraState, CameraUpdateOptions } from './CameraTypes';
import { CameraEvents } from './CameraEvents';
import { type CameraConfig, DEFAULT_CAMERA_CONFIG } from './CameraConfig';
import { CameraValidation } from './CameraValidation';

/**
 * The CameraEngine is the canonical owner of the camera state.
 * It enforces constraints, manages state mutability, and broadcasts events.
 * It does not know about rendering, mapping libraries, or UI.
 */
export class CameraEngine {
  public readonly events: CameraEvents;
  
  private _config: CameraConfig;
  private readonly _state: CameraState;

  constructor(config: Partial<CameraConfig> = {}) {
    this._config = { ...DEFAULT_CAMERA_CONFIG, ...config };
    this.events = new CameraEvents();
    
    // Allocate the zero-allocation state object once
    this._state = {
      latitude: this._config.initialState.latitude,
      longitude: this._config.initialState.longitude,
      altitude: this._config.initialState.altitude,
      pitch: this._config.initialState.pitch,
      bearing: this._config.initialState.bearing,
    };
  }

  /**
   * Instantly jumps the camera to the specified partial state.
   * Validates and applies clamping before committing.
   */
  public jumpTo(options: CameraUpdateOptions): void {
    CameraValidation.applyUpdate(this._state, options, this._state, this._config);
    this.events.dispatchMoved(this._state);
  }

  /**
   * Resets the camera to its initial configured state.
   */
  public reset(): void {
    this._state.latitude = this._config.initialState.latitude;
    this._state.longitude = this._config.initialState.longitude;
    this._state.altitude = this._config.initialState.altitude;
    this._state.pitch = this._config.initialState.pitch;
    this._state.bearing = this._config.initialState.bearing;

    this.events.dispatchReset();
    this.events.dispatchMoved(this._state);
  }

  /**
   * Updates the engine configuration (e.g. constraints).
   * Might clamp current state to new constraints immediately.
   */
  public setConfig(config: Partial<CameraConfig>): void {
    this._config = { ...this._config, ...config };
    
    // Re-apply current state through validation in case bounds shrunk
    CameraValidation.applyUpdate(this._state, {}, this._state, this._config);
    
    this.events.dispatchConfigurationChanged();
    this.events.dispatchMoved(this._state);
  }

  /**
   * Returns a read-only reference to the current camera state.
   * Do not mutate the returned object.
   */
  public getState(): Readonly<CameraState> {
    return this._state;
  }
}
