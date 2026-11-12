import { create } from 'zustand';
import type {
  NaturalQueryResult,
  PlaceCandidate,
} from '../services/naturalQueryApi';
import {
  submitNaturalQuery,
  NaturalQueryApiError,
} from '../services/naturalQueryApi';

interface NaturalQueryState {
  /** The current text in the query input. */
  query: string;
  /** Whether a request is in-flight. */
  loading: boolean;
  /** The last successful result from the backend. */
  result: NaturalQueryResult | null;
  /** Human-readable error message, if any. */
  error: string | null;

  setQuery: (query: string) => void;
  submit: (projectId: string) => Promise<void>;
  clear: () => void;
}

/**
 * Translate HTTP/API errors into clear, user-facing messages.
 */
function friendlyError(err: unknown): string {
  if (err instanceof NaturalQueryApiError) {
    if (err.statusCode === 503) {
      return 'The AI interpreter is currently unavailable. Please try again later.';
    }
    if (err.statusCode === 422) {
      return err.message;
    }
    return err.message;
  }
  if (err instanceof TypeError && err.message.includes('fetch')) {
    return 'Unable to reach the backend. Is the server running?';
  }
  return 'An unexpected error occurred. Please try again.';
}

export const useNaturalQueryStore = create<NaturalQueryState>((set, get) => ({
  query: '',
  loading: false,
  result: null,
  error: null,

  setQuery: (query) => set({ query }),

  submit: async (projectId: string) => {
    const q = get().query.trim();
    if (!q) return;

    set({ loading: true, error: null, result: null });

    try {
      const result = await submitNaturalQuery(projectId, q);
      set({ result, loading: false });
    } catch (err) {
      set({ error: friendlyError(err), loading: false });
    }
  },

  clear: () => set({ query: '', result: null, error: null, loading: false }),
}));

// Re-export types for convenience
export type { NaturalQueryResult, PlaceCandidate };
