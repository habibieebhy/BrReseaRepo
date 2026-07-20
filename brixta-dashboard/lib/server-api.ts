import "server-only";

import { headers as requestHeaders } from "next/headers";

import { auth0, auth0Enabled, dashboardAuthMode } from "@/lib/auth0";

const backend = process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000";

async function authorizationHeaders(): Promise<HeadersInit> {
  if (auth0Enabled) {
    if (!auth0) return {};
    try {
      const { token } = await auth0.getAccessToken();
      return { Authorization: `Bearer ${token}` };
    } catch (error) {
      console.error("[Server API] Failed to get Auth0 Access Token:", error);
      return {};
    }
  }

  if (dashboardAuthMode === "cloudflare-access") {
    const incoming = await requestHeaders();
    const assertion = incoming.get("cf-access-jwt-assertion");
    return assertion ? { "CF-Access-Jwt-Assertion": assertion } : {};
  }

  return {};
}

/**
 * Server-component API client. Browser components must use requestPythonApi so
 * credentials stay inside the same-origin BFF route.
 */
export async function fetchPythonApiServer(
  endpoint: string,
  options?: RequestInit,
): Promise<Record<string, unknown>> {
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  try {
    const response = await fetch(new URL(cleanEndpoint, backend), {
      ...options,
      headers: {
        ...(await authorizationHeaders()),
        ...options?.headers,
      },
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      return {
        status: response.status,
        error:
          typeof body.detail === "string"
            ? body.detail
            : `BRIXTA API returned ${response.status}`,
      };
    }
    return response.json() as Promise<Record<string, unknown>>;
  } catch (error) {
    console.error(`Server API request failed for ${cleanEndpoint}`, error);
    return { status: 502, error: "BRIXTA Core API is unavailable." };
  }
}
