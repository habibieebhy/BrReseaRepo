import { defineConfig } from "drizzle-kit";
import dotenv from "dotenv";

dotenv.config({
  path: "../.env",
});

if (!process.env.DATABASE_URL) {
  throw new Error("DATABASE_URL is missing.");
}

export default defineConfig({
  dialect: "postgresql",

  schema: "./schema.ts",

  out: "./drizzle",

  dbCredentials: {
    url: process.env.DATABASE_URL,
  },

  schemaFilter: ["BrResearch"], // <-- your Neon schema

  verbose: true,

  strict: true,
});