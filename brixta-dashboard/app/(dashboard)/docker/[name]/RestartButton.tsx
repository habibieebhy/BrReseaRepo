// app/(dashboard)/docker/[name]/RestartButton.tsx

"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";

export function RestartButton({ containerName }: { containerName: string }) {
  const [isRestarting, setIsRestarting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleRestart = async () => {
    setIsRestarting(true);
    setMessage(null);
    
    try {
      // Direct client-to-server fetch. Ensure CORS is enabled on Python backend!
      const res = await fetch(`http://localhost:8000/prod/docker/restart/${containerName}`, {
        method: "POST",
      });

      if (!res.ok) {
        throw new Error(`Failed to restart: ${res.statusText}`);
      }

      setMessage("Restart command sent successfully.");
      
      // Optional: Force a page reload after a few seconds to get fresh container states
      setTimeout(() => {
        window.location.reload();
      }, 2000);

    } catch (error: unknown) {
      console.error(error);
      setMessage(error instanceof Error ? error.message : "An error occurred.");
    } finally {
      setIsRestarting(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-2">
      <Button 
        onClick={handleRestart} 
        disabled={isRestarting}
        variant="destructive"
      >
        {isRestarting ? "Restarting..." : "Restart Container"}
      </Button>
      {message && <span className="text-sm text-muted-foreground">{message}</span>}
    </div>
  );
}
