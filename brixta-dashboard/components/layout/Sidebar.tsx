"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  LayoutDashboard,
  Upload,
  Puzzle,
  Database,
  Settings,
  Container,
  Flower2,
  Server,
  Globe2,
  BookOpen,
  BrainCircuit,
} from "lucide-react";

const sections = [
  {
    title: "Workspace",
    items: [
      {
        name: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
      },
      {
        name: "Ingestion",
        href: "/ingestion",
        icon: Upload,
      },
      {
        name: "Sources & Schedules",
        href: "/sources",
        icon: Globe2,
      },
      {
        name: "Knowledge Bases",
        href: "/knowledge",
        icon: BrainCircuit,
      },
      {
        name: "Plugins",
        href: "/plugins",
        icon: Puzzle,
      },
      {
        name: "Settings",
        href: "/settings",
        icon: Settings,
      },
    ],
  },
  {
    title: "Infrastructure",
    items: [
      {
        name: "Docker",
        href: "/docker",
        icon: Container,
      },
      {
        name: "Celery (Jobs)",
        href: "/celery",
        icon: Flower2,
      },
      {
        name: "Storage (MinIO)",
        href: "/storage",
        icon: Database,
      },
      {
        name: "Redis",
        href: "/redis",
        icon: Server,
      },
    ],
  },
  {
    title: "Resources",
    items: [
      {
        name: "Documentation",
        href: "/docs",
        icon: BookOpen,
      },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-72 flex-col border-r bg-background">

      <div className="border-b p-6">

        <h1 className="text-2xl font-bold tracking-tight">
          BRIXTA
        </h1>

        <p className="mt-1 text-sm text-muted-foreground">
          AI Integration Platform
        </p>

      </div>

      <nav className="flex-1 overflow-y-auto p-4">

        {sections.map((section) => (
          <div
            key={section.title}
            className="mb-8"
          >

            <h2 className="mb-3 px-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              {section.title}
            </h2>

            <div className="space-y-1">

              {section.items.map((item) => {

                const Icon = item.icon;

                const active =
                  pathname === item.href;

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`
                      flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all
                      ${
                        active
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-muted"
                      }
                    `}
                  >
                    <Icon size={18} />
                    {item.name}
                  </Link>
                );
              })}
            </div>

          </div>
        ))}

      </nav>

      <div className="border-t p-4">

        <div className="rounded-lg border bg-muted/30 p-3">

          <p className="text-xs text-muted-foreground">
            BRIXTA Core
          </p>

          <p className="font-semibold">
            v2.0.0
          </p>

        </div>

      </div>

    </aside>
  );
}
