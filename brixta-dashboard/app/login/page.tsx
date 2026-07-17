import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const protectedDashboard =
    process.env.BRIXTA_DASHBOARD_AUTH_MODE === "cloudflare-access";
  return (
    <main className="grid min-h-screen place-items-center bg-muted/30 p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>BRIXTA Mission Control</CardTitle>
          <CardDescription>
            {protectedDashboard
              ? "Your identity was verified by Cloudflare Access. BRIXTA will use the same signed session for tenant-scoped API requests."
              : "Local development mode is active. Production must be protected by Cloudflare Access or another configured OIDC/JWT gateway."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button render={<Link href="/dashboard" />} className="w-full">
            {protectedDashboard ? "Open Mission Control" : "Enter local dashboard"}
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
