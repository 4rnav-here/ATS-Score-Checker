import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js Middleware — route protection for authenticated pages.
 *
 * Checks for access_token cookie (set as httpOnly by the backend).
 * Redirects unauthenticated users to /login.
 *
 * Protected routes:
 *   /analyze, /results, /settings
 *
 * Public routes:
 *   /, /login, /verify-otp, /verify-2fa
 */

// Routes that require authentication
const PROTECTED_PATHS = ["/analyze", "/results", "/settings"];

// Routes that should redirect to /analyze if already logged in
const AUTH_PATHS = ["/login", "/verify-otp", "/verify-2fa"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const accessToken = request.cookies.get("access_token")?.value;
  const isAuthenticated = !!accessToken;

  // Check if current path is protected
  const isProtectedRoute = PROTECTED_PATHS.some((path) =>
    pathname.startsWith(path)
  );

  // Check if current path is an auth page
  const isAuthRoute = AUTH_PATHS.some((path) => pathname === path);

  // Redirect unauthenticated users from protected routes to /login
  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect authenticated users from auth pages to /analyze
  if (isAuthRoute && isAuthenticated) {
    return NextResponse.redirect(new URL("/analyze", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all routes except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico
     * - public files
     */
    "/((?!_next/static|_next/image|favicon.ico|public).*)",
  ],
};
