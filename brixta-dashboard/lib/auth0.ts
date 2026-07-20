import { Auth0Client } from "@auth0/nextjs-auth0/server";
import { NextResponse } from "next/server";

export type DashboardAuthMode = "none" | "auth0" | "cloudflare-access";

const configuredMode = (process.env.BRIXTA_DASHBOARD_AUTH_MODE || "none").toLowerCase();

if (!["none", "auth0", "cloudflare-access"].includes(configuredMode)) {
  throw new Error("BRIXTA_DASHBOARD_AUTH_MODE must be none, auth0, or cloudflare-access.");
}

export const dashboardAuthMode = configuredMode as DashboardAuthMode;
export const auth0Enabled = dashboardAuthMode === "auth0";

type AuthErrorDetails = {
  name?: string;
  code?: string;
  message?: string;
  cause?: AuthErrorDetails | string;
};

function authErrorDetails(value: unknown): AuthErrorDetails | string {
  if (!(value instanceof Error)) return String(value);
  const error = value as Error & { code?: string; cause?: unknown };
  return {
    name: error.name,
    code: error.code,
    message: error.message,
    cause: error.cause ? authErrorDetails(error.cause) : undefined,
  };
}

function requireAuth0Configuration() {
  const required = [
    "AUTH0_DOMAIN",
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET",
    "AUTH0_SECRET",
    "APP_BASE_URL",
    "AUTH0_AUDIENCE",
  ] as const;
  const missing = required.filter((name) => !process.env[name]?.trim());
  if (missing.length) {
    throw new Error(`Auth0 dashboard mode is missing: ${missing.join(", ")}`);
  }
}

if (auth0Enabled) {
  requireAuth0Configuration();
}

export const auth0 = auth0Enabled
  ? new Auth0Client({
      authorizationParameters: {
        audience: process.env.AUTH0_AUDIENCE,
        // Add BRIXTA API scopes through AUTH0_SCOPE only after those
        // permissions exist on the Auth0 Custom API.
        scope: process.env.AUTH0_SCOPE || "openid profile email offline_access",
      },
      signInReturnToPath: "/dashboard",
      enableAccessTokenEndpoint: false,
      async onCallback(error, context) {
        const appBaseUrl = context.appBaseUrl ?? process.env.APP_BASE_URL!;
        if (error) {
          // The SDK's top-level authorization error is intentionally generic.
          // Log its nested OAuth cause on the server so configuration failures
          // such as an unknown audience are diagnosable without exposing those
          // details in a browser response.
          console.error("Auth0 callback failed:", authErrorDetails(error));
          return NextResponse.redirect(
            new URL("/login?error=authorization_failed", appBaseUrl),
          );
        }
        return NextResponse.redirect(
          new URL(context.returnTo || "/dashboard", appBaseUrl),
        );
      },
      session: {
        rolling: true,
        absoluteDuration: 60 * 60 * 12,
        inactivityDuration: 60 * 60 * 2,
      },
    })
  : null;
