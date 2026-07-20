import type { NextRequest } from "next/server";
import { auth0, auth0Enabled } from "@/lib/auth0";

const backend = process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  if (auth0Enabled && !["GET", "HEAD", "OPTIONS"].includes(request.method)) {
    const configuredOrigin = process.env.APP_BASE_URL;
    const requestOrigin = request.headers.get("origin");
    if (!configuredOrigin || !requestOrigin || requestOrigin !== new URL(configuredOrigin).origin) {
      return Response.json({ detail: "Cross-site request rejected." }, { status: 403 });
    }
  }
  const { path } = await context.params;
  const target = new URL(`/${path.join("/")}`, backend);
  target.search = request.nextUrl.search;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("cookie");
  if (auth0Enabled) {
    if (!auth0) {
      return Response.json({ detail: "Dashboard authentication is unavailable." }, { status: 503 });
    }
    try {
      const { token } = await auth0.getAccessToken();
      headers.set("authorization", `Bearer ${token}`);
    } catch (error) {
      console.error("[Auth0 Proxy Error] Failed to get access token:", error);
      return Response.json({ detail: "Your BRIXTA session has expired." }, { status: 401 });
    }
  }
  try {
    const response = await fetch(target, {
      method: request.method,
      headers,
      body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(),
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    return new Response(response.body, { status: response.status, headers: response.headers });
  } catch (error) {
    console.error("BRIXTA API proxy failed", error);
    return Response.json(
      { detail: "BRIXTA Core API is unavailable." },
      { status: 502 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
