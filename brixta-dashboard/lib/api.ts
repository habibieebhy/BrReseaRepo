// brixta-dashboard/lib/api.ts

export async function fetchPythonApi(endpoint: string, options?: RequestInit) {
  // Fallback to localhost if the env var is missing during build/dev
  const baseUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";
  
  // Ensure we don't end up with double slashes like http://localhost:8000//api
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;

  try {
    const res = await fetch(`${baseUrl}${cleanEndpoint}`, {
      ...options,
    });
    
    if (!res.ok) {
      throw new Error(`API Error ${res.status}: ${res.statusText} at ${cleanEndpoint}`);
    }
    
    return await res.json();
  } catch (error) {
    console.error(`Fetch failed for ${cleanEndpoint}:`, error);
    return { error: `Failed to connect to Python backend at ${cleanEndpoint}` };
  }
}

export const browserApiUrl =
  process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL || "/api/core";

export async function requestPythonApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const isFormData = options?.body instanceof FormData;
  const response = await fetch(`${browserApiUrl}${cleanEndpoint}`, {
    ...options,
    headers: isFormData ? options?.headers : { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `BRIXTA API returned ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
