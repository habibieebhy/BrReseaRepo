import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function MarketplacePage() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div><h1 className="text-3xl font-bold tracking-tight">Marketplace</h1><p className="text-muted-foreground">The installation lifecycle is the next control-plane module.</p></div>
      <Card><CardHeader><CardTitle>Registry before marketplace</CardTitle><CardDescription>Runtime selection is working; package trust, manifests, dependency checks, enable/disable, and uninstall safety are not implemented yet.</CardDescription></CardHeader><CardContent><p className="text-sm text-muted-foreground">For now, installed plugins are declared by the backend registry and visible in the Plugin catalog. This page is intentionally informational instead of presenting fake install buttons.</p></CardContent></Card>
    </div>
  );
}
