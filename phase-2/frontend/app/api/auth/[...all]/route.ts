/**
 * Better Auth API Route Handler
 *
 * This catch-all route handles all Better Auth requests:
 * - POST /api/auth/sign-up
 * - POST /api/auth/sign-in
 * - POST /api/auth/sign-out
 * - GET /api/auth/session
 * - GET /api/auth/.well-known/jwks.json (for JWT verification)
 *
 * The route is automatically handled by Better Auth's toNextJsHandler.
 */

import { auth } from "@/lib/auth-server";
import { toNextJsHandler } from "better-auth/next-js";

/**
 * Export GET and POST handlers from Better Auth
 *
 * These handlers automatically process all Better Auth requests
 * based on the URL path and HTTP method.
 */
export const { GET, POST } = toNextJsHandler(auth.handler);

/**
 * Runtime configuration
 * Use Node.js runtime (not Edge) for database connections
 */
export const runtime = "nodejs";
