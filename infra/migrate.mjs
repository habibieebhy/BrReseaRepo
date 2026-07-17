import { createHash } from "node:crypto";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import postgres from "postgres";

const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  throw new Error("DATABASE_URL is required for BRIXTA migrations.");
}

const here = path.dirname(fileURLToPath(import.meta.url));
const migrationDirectory = path.join(here, "migrations");
const sql = postgres(databaseUrl, {
  max: 1,
  prepare: false,
  ssl: databaseUrl.includes("sslmode=require") ? "require" : undefined,
});

try {
  await sql.unsafe('CREATE EXTENSION IF NOT EXISTS vector');
  await sql.unsafe('CREATE SCHEMA IF NOT EXISTS "BrResearch"');
  await sql.unsafe(`
    CREATE TABLE IF NOT EXISTS "BrResearch"."_brixta_migrations" (
      "name" text PRIMARY KEY,
      "checksum" text NOT NULL,
      "applied_at" timestamp with time zone NOT NULL DEFAULT now()
    )
  `);

  const files = (await readdir(migrationDirectory))
    .filter((name) => name.endsWith(".sql"))
    .sort();

  for (const name of files) {
    const source = await readFile(path.join(migrationDirectory, name), "utf8");
    const checksum = createHash("sha256").update(source).digest("hex");
    const rows = await sql`
      SELECT checksum
      FROM "BrResearch"."_brixta_migrations"
      WHERE name = ${name}
    `;
    if (rows.length) {
      if (rows[0].checksum !== checksum) {
        throw new Error(
          `Applied migration ${name} changed. Add a new migration instead of editing history.`,
        );
      }
      console.log(`skip ${name}`);
      continue;
    }

    await sql.begin(async (transaction) => {
      await transaction.unsafe(source);
      await transaction`
        INSERT INTO "BrResearch"."_brixta_migrations" (name, checksum)
        VALUES (${name}, ${checksum})
      `;
    });
    console.log(`applied ${name}`);
  }
} finally {
  await sql.end({ timeout: 5 });
}
