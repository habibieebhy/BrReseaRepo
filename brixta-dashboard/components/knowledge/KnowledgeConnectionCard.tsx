"use client";

import {
  Check,
  ChevronDown,
  Copy,
  Database,
  ExternalLink,
  KeyRound,
  MessageSquareText,
  Search,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { KnowledgeBase } from "@/types/types";
import { requestPythonApi } from "@/lib/api";

interface McpStatus {
  connected: boolean;
  mode: "local" | "production" | "disconnected";
  mcp_url: string | null;
  authenticated: boolean;
  shared_gateway: boolean;
}

function CopyValue({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }
  return (
    <Button type="button" size="sm" variant="outline" onClick={copy}>
      {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? "Copied" : label}
    </Button>
  );
}

export default function KnowledgeConnectionCard({ knowledgeBase }: { knowledgeBase: KnowledgeBase }) {
  const [status, setStatus] = useState<McpStatus | null>(null);
  const [enabled, setEnabled] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      requestPythonApi<McpStatus>("/prod/mcp/status"),
      requestPythonApi<{ enabled: boolean }>(`/prod/knowledge/${knowledgeBase.id}/access`),
    ]).then(([connection, access]) => {
      setStatus(connection);
      setEnabled(access.enabled);
    }).catch(() => setStatus(null));
  }, [knowledgeBase.id]);

  async function toggleAccess() {
    setSaving(true);
    try {
      const response = await requestPythonApi<{ enabled: boolean }>(`/prod/knowledge/${knowledgeBase.id}/access`, {
        method: "PUT",
        body: JSON.stringify({ enabled: !enabled }),
      });
      setEnabled(response.enabled);
    } finally {
      setSaving(false);
    }
  }

  const gatewayOnline = Boolean(status?.connected && status.authenticated);
  return (
    <Card className="overflow-hidden border-primary/20 bg-gradient-to-br from-card via-card to-primary/5 shadow-sm">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2"><Database size={19} /> Knowledge base ready</CardTitle>
            <CardDescription>{knowledgeBase.chunk_count} searchable chunks · {knowledgeBase.embedding_model} · {knowledgeBase.embedding_dimension}d</CardDescription>
          </div>
          <div className="flex gap-2"><Badge className="gap-1"><ShieldCheck size={12} /> ready</Badge>{gatewayOnline && <Badge variant="secondary">MCP online</Badge>}</div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          <Button render={<Link href={`/knowledge/${knowledgeBase.id}#retrieval`} />}>
            <Search size={15} /> Search knowledge
          </Button>
          {gatewayOnline && enabled ? (
            <Button render={<a href="https://chatgpt.com/" target="_blank" rel="noreferrer" />}>
              <MessageSquareText size={15} /> Use with ChatGPT
            </Button>
          ) : gatewayOnline ? (
            <Button variant="outline" onClick={toggleAccess} disabled={saving}>
              <MessageSquareText size={15} /> {saving ? "Enabling…" : "Enable for ChatGPT"}
            </Button>
          ) : (
            <Button variant="outline" render={<Link href="/docs#chatgpt" />}>
              <MessageSquareText size={15} /> Connect ChatGPT
            </Button>
          )}
        </div>

        <div className="rounded-2xl border bg-muted/35 p-4">
          <div className="flex items-start gap-3">
            <KeyRound className="mt-0.5 text-primary" size={18} />
            <div>
              <p className="text-sm font-medium">Access scope</p>
              <p className="mt-1 text-xs text-muted-foreground">
                This knowledge base belongs to tenant <strong className="text-foreground">{knowledgeBase.tenant_id}</strong>.
                The shared MCP gateway derives tenant access from the authenticated connection. MCP access is currently <strong className="text-foreground">{enabled ? "enabled" : "disabled"}</strong>.
              </p>
              <Button className="mt-3" size="sm" variant="outline" onClick={toggleAccess} disabled={saving}>
                {saving ? "Saving…" : enabled ? "Disable MCP access" : "Enable MCP access"}
              </Button>
            </div>
          </div>
        </div>

        <details className="group rounded-2xl border bg-background/60 p-4">
          <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium">
            Developer details
            <ChevronDown className="transition-transform group-open:rotate-180" size={16} />
          </summary>
          <div className="mt-4 space-y-3">
            <div className="rounded-xl bg-muted p-3">
              <p className="text-xs text-muted-foreground">Stable BRIXTA handle</p>
              <code className="mt-1 block break-all text-xs">{knowledgeBase.uri}</code>
            </div>
            <div className="flex flex-wrap gap-2">
              <CopyValue value={knowledgeBase.uri} label="Copy handle" />
              <CopyValue value={knowledgeBase.retrieval_url} label="Copy retrieval API" />
              <CopyValue value={status?.mcp_url || knowledgeBase.mcp_url} label="Copy shared MCP URL" />
              <Button size="sm" variant="ghost" render={<a href={knowledgeBase.manifest_url} target="_blank" rel="noreferrer" />}>
                Manifest <ExternalLink size={13} />
              </Button>
            </div>
          </div>
        </details>
      </CardContent>
    </Card>
  );
}
