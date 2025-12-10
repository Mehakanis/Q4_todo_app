/**
 * Better Auth Server Configuration
 *
 * This file configures the Better Auth server with:
 * - PostgreSQL database connection (shared with FastAPI backend)
 * - Email/password authentication
 * - JWT plugin for token generation
 * - Next.js cookies plugin for session management
 */

import { betterAuth } from "better-auth";
import { nextCookies } from "better-auth/next-js";
import { jwt } from "better-auth/plugins";
import { Pool } from "pg";

// Validate required environment variables
if (!process.env.DATABASE_URL) {
  throw new Error("DATABASE_URL environment variable is required");
}

if (!process.env.BETTER_AUTH_SECRET) {
  throw new Error("BETTER_AUTH_SECRET environment variable is required");
}

/**
 * PostgreSQL connection pool
 * Shared with FastAPI backend for user authentication
 */
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10, // Maximum number of clients in the pool
  idleTimeoutMillis: 30000, // Close idle clients after 30 seconds
  connectionTimeoutMillis: 2000, // Return an error after 2 seconds if connection cannot be established
});

/**
 * Better Auth configuration
 *
 * Features:
 * - Email/password authentication
 * - JWT tokens (7-day expiration)
 * - Session management via cookies
 * - PostgreSQL database for user storage
 */
export const auth = betterAuth({
  // Database configuration
  database: pool,

  // Secret key for signing tokens and cookies
  secret: process.env.BETTER_AUTH_SECRET,

  // Base URL for authentication endpoints
  baseURL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",

  // Email and password authentication
  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false, // Set to true in production with email service
  },

  // Session configuration
  session: {
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // Cache session in cookie for 5 minutes
    },
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // Update session every 24 hours
  },

  // Trusted origins for CORS
  trustedOrigins: [
    process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  ],

  // Plugins (order matters - nextCookies must be last)
  plugins: [
    // JWT plugin for token generation
    jwt({
      expiresIn: 60 * 60 * 24 * 7, // 7 days
      issuer: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
    }),

    // Next.js cookies plugin (MUST be last)
    nextCookies(),
  ],
});

/**
 * Export auth handler types for API routes
 */
export type Auth = typeof auth;
