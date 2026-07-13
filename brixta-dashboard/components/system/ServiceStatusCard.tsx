import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function ServiceStatusCard({ name, description, healthy, detail, action }: { name: string; description: string; healthy: boolean | null; detail?: string; action?: React.ReactNode }) {
  const label = healthy === null ? "not connected" : healthy ? "running" : "unavailable";
  return <Card><CardHeader><div className="flex items-start justify-between gap-3"><div><CardTitle>{name}</CardTitle><CardDescription>{description}</CardDescription></div><Badge variant={healthy ? "default" : healthy === null ? "secondary" : "destructive"}>{label}</Badge></div></CardHeader><CardContent className="space-y-3">{detail && <p className="break-words text-xs text-muted-foreground">{detail}</p>}{action}</CardContent></Card>;
}
