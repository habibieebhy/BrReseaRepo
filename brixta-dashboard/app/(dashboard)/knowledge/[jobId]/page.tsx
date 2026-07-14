"use client";

import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft, LoaderCircle, Search } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import KnowledgeConnectionCard from "@/components/knowledge/KnowledgeConnectionCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { requestPythonApi } from "@/lib/api";
import type { KnowledgeBase } from "@/types/types";

interface SearchResult { id: string; title: string; text: string; score: number; url: string }

export default function KnowledgeDetailPage() {
  const params = useParams<{ jobId: string }>();
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    requestPythonApi<{ knowledge_base: KnowledgeBase }>(`/prod/knowledge/${params.jobId}`)
      .then((value) => setKnowledgeBase(value.knowledge_base))
      .catch((reason: Error) => setError(reason.message));
  }, [params.jobId]);

  async function search(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const response = await requestPythonApi<{ results: SearchResult[] }>(`/prod/knowledge/${params.jobId}/search`, { method: "POST", body: JSON.stringify({ query, limit: 6 }) });
      setResults(response.results);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Search failed.");
    } finally { setBusy(false); }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6 md:p-8">
      <Button variant="ghost" render={<Link href="/knowledge" />}><ArrowLeft size={15} /> All knowledge bases</Button>
      {knowledgeBase && <KnowledgeConnectionCard knowledgeBase={knowledgeBase} />}
      <Card id="retrieval">
        <CardHeader><CardTitle>Retrieval playground</CardTitle><CardDescription>Test the same semantic search exposed to local model UIs and the MCP server.</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={search} className="flex gap-2"><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask about this knowledge base…" required /><Button type="submit" disabled={busy}>{busy ? <LoaderCircle className="animate-spin" size={16} /> : <Search size={16} />} Search</Button></form>
          {error && <div className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
          <div className="space-y-3">{results.map((item) => <div key={item.id} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-3"><p className="font-medium">{item.title}</p><span className="rounded-full bg-muted px-2 py-1 text-xs">{item.score.toFixed(3)}</span></div><p className="mt-2 line-clamp-5 whitespace-pre-wrap text-sm text-muted-foreground">{item.text}</p></div>)}</div>
          {!busy && results.length === 0 && <p className="text-sm text-muted-foreground">No search has been run yet.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
