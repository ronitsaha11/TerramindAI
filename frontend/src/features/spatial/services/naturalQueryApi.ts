/**
 * API client for the natural-language query endpoint.
 *
 * Talks to POST /api/v1/projects/{project_id}/query/natural, which is the
 * single entry point for the Phase 5 NLQ pipeline. All geographic computation
 * happens server-side; this client only carries the question and renders the
 * answer.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/** A place candidate returned when the query is ambiguous. */
export interface PlaceCandidate {
  feature_id: string;
  feature_name: string;
  dataset_id: string;
  dataset_name: string;
  category: string | null;
  geometry_type: string;
  lon: number;
  lat: number;
}

/** The interpreted intent — what Claude understood the question to mean. */
export interface SpatialInterpretation {
  operation: 'nearby' | 'contains' | 'intersects';
  reference_place: string | null;
  target_category: string | null;
  target_dataset: string | null;
  distance_meters: number | null;
}

/** The full response shape from the NLQ endpoint. */
export interface NaturalQueryResult {
  status: 'ok' | 'ambiguous' | 'unresolved';
  query: string;
  answer: string;
  interpretation: SpatialInterpretation | null;
  result: GeoJSON.FeatureCollection | null;
  focus: { lon: number; lat: number } | null;
  candidates: PlaceCandidate[];
}

/** Wrapper matching the backend's SuccessResponse<T>. */
interface ApiResponse<T> {
  success: boolean;
  data: T;
}

export class NaturalQueryApiError extends Error {
  readonly statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = 'NaturalQueryApiError';
    this.statusCode = statusCode;
  }
}


/**
 * Send a natural-language question to the backend NLQ pipeline.
 *
 * @throws {NaturalQueryApiError} on HTTP errors (503, 422, etc.)
 */
export async function submitNaturalQuery(
  projectId: string,
  query: string,
): Promise<NaturalQueryResult> {
  const url = `${API_BASE_URL}/projects/${projectId}/query/natural`;

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
      // If JSON parsing fails, use the generic message.
    }
    throw new NaturalQueryApiError(detail, res.status);
  }

  const body: ApiResponse<NaturalQueryResult> = await res.json();
  return body.data;
}
