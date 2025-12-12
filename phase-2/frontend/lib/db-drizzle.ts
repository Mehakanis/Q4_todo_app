/**
 * Drizzle ORM Database Connection
 *
 * This file creates a Drizzle ORM instance using Neon Serverless driver.
 * Features:
 * - Serverless PostgreSQL connection via Neon
 * - Connection pooling for better performance
 * - Type-safe database operations
 * - Integrated with Better Auth schema
 */

import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";
import * as schema from "@/drizzle/schema";

// Validate DATABASE_URL at module load time
if (!process.env.DATABASE_URL) {
  throw new Error("DATABASE_URL environment variable is required");
}

/**
 * Create Neon SQL client
 * This uses HTTP connection for serverless environments
 */
const sql = neon(process.env.DATABASE_URL);

/**
 * Drizzle database instance
 * Includes Better Auth schema for type-safe queries
 */
export const db = drizzle(sql, { schema });

/**
 * Type export for database instance
 */
export type Database = typeof db;
