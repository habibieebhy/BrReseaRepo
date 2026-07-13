import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-muted/30 p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>BRIXTA Mission Control</CardTitle>
          <CardDescription>Authentication is not enabled in this self-hosted MVP.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button render={<Link href="/dashboard" />} className="w-full">Enter local dashboard</Button>
        </CardContent>
      </Card>
    </main>
  );
}
