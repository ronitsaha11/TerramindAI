import { RenderingLifecycleState } from '../RenderingLifecycle';

export interface RenderingStoreState {
  lifecycleState: RenderingLifecycleState;
  
  setLifecycleState: (state: RenderingLifecycleState) => void;
}
