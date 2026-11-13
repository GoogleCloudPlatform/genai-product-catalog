// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { createHash, timingSafeEqual } from 'crypto';
import type { ErrorRequestHandler, NextFunction, Request, RequestHandler, Response } from 'express';

export interface SocketHandshakeLike {
  address?: string;
  auth?: Record<string, unknown>;
  headers?: Record<string, string | string[] | undefined>;
}

export interface SocketLike {
  id: string;
  handshake?: SocketHandshakeLike;
  conn?: { remoteAddress?: string };
  use(fn: (packet: unknown[], next: (err?: Error) => void) => void): unknown;
}

export interface SocketServerLike<TSocket extends SocketLike = SocketLike> {
  use(fn: (socket: TSocket, next: (err?: Error) => void) => void): unknown;
}

export const DEFAULT_JSON_BODY_LIMIT = '1mb';
export const DEFAULT_SOCKET_MAX_BUFFER_BYTES = 1_048_576; // 1 MiB
export const MAX_ALLOWED_SOCKET_BUFFER_BYTES = 10 * 1_048_576; // 10 MiB
export const DEFAULT_RATE_LIMIT_WINDOW_MS = 60_000;
export const DEFAULT_HTTP_RATE_LIMIT_MAX = 60;
export const DEFAULT_SOCKET_CONN_RATE_LIMIT_MAX = 20;
export const DEFAULT_SOCKET_EVENT_RATE_LIMIT_MAX = 30;

export const DEFAULT_LOCAL_DEV_ORIGINS: readonly string[] = Object.freeze([
  'http://localhost:4200',
  'http://127.0.0.1:4200',
  'http://localhost:3000',
  'http://127.0.0.1:3000',
]);

export function resolveJsonBodyLimit(
  env: NodeJS.ProcessEnv = process.env
): string {
  const configured = env.JSON_BODY_LIMIT?.trim();
  if (!configured) {
    return DEFAULT_JSON_BODY_LIMIT;
  }
  if (!/^\d+(?:\.\d+)?\s*(?:b|kb|mb)?$/i.test(configured)) {
    return DEFAULT_JSON_BODY_LIMIT;
  }
  return configured;
}

export function resolveSocketMaxBufferBytes(
  env: NodeJS.ProcessEnv = process.env
): number {
  const raw = env.SOCKET_MAX_BUFFER_BYTES?.trim();
  if (!raw) {
    return DEFAULT_SOCKET_MAX_BUFFER_BYTES;
  }
  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return DEFAULT_SOCKET_MAX_BUFFER_BYTES;
  }
  return Math.min(Math.floor(parsed), MAX_ALLOWED_SOCKET_BUFFER_BYTES);
}

function normalizeOrigin(candidate: string): string | null {
  const trimmed = candidate.trim();
  if (!trimmed || trimmed === '*') {
    return null;
  }
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return null;
    }
    return parsed.origin;
  } catch {
    return null;
  }
}

export function getAllowedOrigins(
  env: NodeJS.ProcessEnv = process.env
): Set<string> {
  const raw = env.ALLOWED_ORIGINS;
  if (raw === undefined) {
    if (env.NODE_ENV === 'production') {
      return new Set<string>();
    }
    return new Set<string>(DEFAULT_LOCAL_DEV_ORIGINS);
  }

  const allowed = new Set<string>();
  for (const entry of raw.split(',')) {
    const normalized = normalizeOrigin(entry);
    if (normalized) {
      allowed.add(normalized);
    }
  }
  return allowed;
}

export function createExpressCorsOriginValidator(
  envGetter: () => NodeJS.ProcessEnv = () => process.env
): (
  requestOrigin: string | undefined,
  callback: (err: Error | null, allow?: boolean) => void
) => void {
  return (requestOrigin, callback) => {
    if (!requestOrigin) {
      callback(null, false);
      return;
    }
    const normalized = normalizeOrigin(requestOrigin);
    const allowed = getAllowedOrigins(envGetter());
    if (normalized && allowed.has(normalized)) {
      callback(null, true);
      return;
    }
    callback(null, false);
  };
}

export function createSocketCorsOriginValidator(
  envGetter: () => NodeJS.ProcessEnv = () => process.env
): (
  requestOrigin: string | undefined,
  callback: (err: Error | null, allow?: boolean) => void
) => void {
  return (requestOrigin, callback) => {
    const env = envGetter();
    if (!requestOrigin) {
      if (env.NODE_ENV === 'production') {
        callback(new Error('Origin header required'), false);
      } else {
        callback(null, true);
      }
      return;
    }
    const normalized = normalizeOrigin(requestOrigin);
    const allowed = getAllowedOrigins(env);
    if (normalized && allowed.has(normalized)) {
      callback(null, true);
      return;
    }
    callback(new Error('Origin not allowed by CORS'), false);
  };
}

export const securityHeadersMiddleware: RequestHandler = (
  _req: Request,
  res: Response,
  next: NextFunction
): void => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=()'
  );
  res.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; frame-ancestors 'none'"
  );
  next();
};

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  retryAfterSeconds: number;
}

export class SlidingWindowRateLimiter {
  private readonly buckets = new Map<string, number[]>();
  private readonly windowMs: number;
  private readonly maxRequests: number;
  private readonly maxTrackedKeys: number;

  constructor(options: {
    windowMs?: number;
    maxRequests?: number;
    maxTrackedKeys?: number;
  } = {}) {
    this.windowMs =
      options.windowMs && options.windowMs > 0
        ? options.windowMs
        : DEFAULT_RATE_LIMIT_WINDOW_MS;
    this.maxRequests =
      options.maxRequests && options.maxRequests > 0
        ? options.maxRequests
        : DEFAULT_HTTP_RATE_LIMIT_MAX;
    this.maxTrackedKeys =
      options.maxTrackedKeys && options.maxTrackedKeys > 0
        ? options.maxTrackedKeys
        : 10_000;
  }

  public check(key: string, now: number = Date.now()): RateLimitResult {
    const cutoff = now - this.windowMs;
    const existing = this.buckets.get(key);
    const active = existing ? existing.filter((ts) => ts > cutoff) : [];

    if (active.length >= this.maxRequests) {
      this.buckets.set(key, active);
      const oldest = active[0] ?? now;
      const retryAfterMs = Math.max(1000, oldest + this.windowMs - now);
      return {
        allowed: false,
        remaining: 0,
        retryAfterSeconds: Math.ceil(retryAfterMs / 1000),
      };
    }

    if (!existing && this.buckets.size >= this.maxTrackedKeys) {
      this.pruneExpired(cutoff);
      if (this.buckets.size >= this.maxTrackedKeys) {
        const oldestKey = this.buckets.keys().next().value;
        if (oldestKey !== undefined) {
          this.buckets.delete(oldestKey);
        }
      }
    }

    active.push(now);
    this.buckets.set(key, active);
    return {
      allowed: true,
      remaining: Math.max(0, this.maxRequests - active.length),
      retryAfterSeconds: 0,
    };
  }

  public reset(): void {
    this.buckets.clear();
  }

  private pruneExpired(cutoff: number): void {
    for (const [bucketKey, timestamps] of this.buckets.entries()) {
      const filtered = timestamps.filter((ts) => ts > cutoff);
      if (filtered.length === 0) {
        this.buckets.delete(bucketKey);
      } else {
        this.buckets.set(bucketKey, filtered);
      }
    }
  }
}

function parsePositiveInt(
  raw: string | undefined,
  fallback: number
): number {
  if (!raw) {
    return fallback;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function createApiRateLimitMiddleware(
  limiter?: SlidingWindowRateLimiter,
  envGetter: () => NodeJS.ProcessEnv = () => process.env
): RequestHandler {
  const env = envGetter();
  const activeLimiter =
    limiter ??
    new SlidingWindowRateLimiter({
      windowMs: parsePositiveInt(
        env.RATE_LIMIT_WINDOW_MS,
        DEFAULT_RATE_LIMIT_WINDOW_MS
      ),
      maxRequests: parsePositiveInt(
        env.RATE_LIMIT_MAX_REQUESTS,
        DEFAULT_HTTP_RATE_LIMIT_MAX
      ),
    });
  const limitHeaderVal = parsePositiveInt(
    env.RATE_LIMIT_MAX_REQUESTS,
    DEFAULT_HTTP_RATE_LIMIT_MAX
  );

  return (req: Request, res: Response, next: NextFunction): void => {
    const clientKey = req.ip || req.socket?.remoteAddress || 'unknown';
    const verdict = activeLimiter.check(clientKey);
    res.setHeader('X-RateLimit-Limit', String(limitHeaderVal));
    res.setHeader('X-RateLimit-Remaining', String(verdict.remaining));
    if (!verdict.allowed) {
      res.setHeader('Retry-After', String(verdict.retryAfterSeconds));
      res.status(429).json({ error: 'Too many requests' });
      return;
    }
    next();
  };
}

function sha256Digest(input: string): Buffer {
  return createHash('sha256').update(input, 'utf8').digest();
}

export function timingSafeTokenMatches(
  providedToken: string,
  expectedSecrets: readonly string[]
): boolean {
  if (!providedToken || expectedSecrets.length === 0) {
    return false;
  }
  const providedHash = sha256Digest(providedToken);
  let matched = false;
  for (const secret of expectedSecrets) {
    if (!secret) {
      continue;
    }
    const secretHash = sha256Digest(secret);
    if (timingSafeEqual(providedHash, secretHash)) {
      matched = true;
    }
  }
  return matched;
}

function getConfiguredTokens(env: NodeJS.ProcessEnv): string[] {
  const tokens: string[] = [];
  const primary = env.API_AUTH_TOKEN?.trim();
  if (primary) {
    tokens.push(primary);
  }
  const extra = env.SERVICE_API_KEYS?.trim();
  if (extra) {
    for (const entry of extra.split(',')) {
      const trimmed = entry.trim();
      if (!trimmed) {
        continue;
      }
      const colonIdx = trimmed.indexOf(':');
      const secret = colonIdx >= 0 ? trimmed.slice(colonIdx + 1).trim() : trimmed;
      if (secret) {
        tokens.push(secret);
      }
    }
  }
  return tokens;
}

function extractBearerToken(authorizationHeader: string | undefined): {
  token: string | null;
  malformed: boolean;
} {
  if (!authorizationHeader) {
    return { token: null, malformed: false };
  }
  const match = /^Bearer\s+(\S+)$/i.exec(authorizationHeader.trim());
  if (!match) {
    return { token: null, malformed: true };
  }
  return { token: match[1], malformed: false };
}

function hasValidIapIdentity(
  headers: Record<string, string | string[] | undefined>,
  env: NodeJS.ProcessEnv
): boolean {
  if (env.TRUST_IAP_HEADERS !== 'true') {
    return false;
  }
  const emailHeader = headers['x-goog-authenticated-user-email'];
  const idHeader = headers['x-goog-authenticated-user-id'];
  const email = Array.isArray(emailHeader) ? emailHeader[0] : emailHeader;
  const userId = Array.isArray(idHeader) ? idHeader[0] : idHeader;
  return Boolean(email && email.trim().length > 0 && userId && userId.trim().length > 0);
}

export function createApiAuthMiddleware(
  envGetter: () => NodeJS.ProcessEnv = () => process.env
): RequestHandler {
  return (req: Request, res: Response, next: NextFunction): void => {
    const env = envGetter();
    const requestOrigin = req.headers.origin;
    if (requestOrigin) {
      const normalizedOrigin = normalizeOrigin(requestOrigin);
      const allowedOrigins = getAllowedOrigins(env);
      if (!normalizedOrigin || !allowedOrigins.has(normalizedOrigin)) {
        res.status(403).json({ error: 'Origin not allowed' });
        return;
      }
    }

    const configuredTokens = getConfiguredTokens(env);
    const trustIap = env.TRUST_IAP_HEADERS === 'true';

    if (configuredTokens.length === 0 && !trustIap) {
      res.status(503).json({ error: 'Service authentication is not configured' });
      return;
    }

    if (hasValidIapIdentity(req.headers, env)) {
      next();
      return;
    }

    const { token: bearerToken, malformed } = extractBearerToken(
      req.headers.authorization
    );
    const rawApiKey = req.headers['x-api-key'];
    const apiKey = (Array.isArray(rawApiKey) ? rawApiKey[0] : rawApiKey)?.trim() || null;

    if (malformed && !apiKey) {
      res.setHeader('WWW-Authenticate', 'Bearer');
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const candidate = bearerToken || apiKey;
    if (!candidate || !timingSafeTokenMatches(candidate, configuredTokens)) {
      res.setHeader('WWW-Authenticate', 'Bearer');
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    next();
  };
}

export function attachSocketSecurity<TSocket extends SocketLike = SocketLike>(
  io: SocketServerLike<TSocket>,
  options: {
    envGetter?: () => NodeJS.ProcessEnv;
    connectionLimiter?: SlidingWindowRateLimiter;
    eventLimiter?: SlidingWindowRateLimiter;
  } = {}
): {
  connectionLimiter: SlidingWindowRateLimiter;
  eventLimiter: SlidingWindowRateLimiter;
} {
  const envGetter = options.envGetter ?? (() => process.env);
  const env = envGetter();
  const windowMs = parsePositiveInt(
    env.RATE_LIMIT_WINDOW_MS,
    DEFAULT_RATE_LIMIT_WINDOW_MS
  );
  const connectionLimiter =
    options.connectionLimiter ??
    new SlidingWindowRateLimiter({
      windowMs,
      maxRequests: parsePositiveInt(
        env.SOCKET_CONN_RATE_LIMIT_MAX,
        DEFAULT_SOCKET_CONN_RATE_LIMIT_MAX
      ),
    });
  const eventLimiter =
    options.eventLimiter ??
    new SlidingWindowRateLimiter({
      windowMs,
      maxRequests: parsePositiveInt(
        env.SOCKET_EVENT_RATE_LIMIT_MAX,
        DEFAULT_SOCKET_EVENT_RATE_LIMIT_MAX
      ),
    });

  // Rate limit incoming Socket.IO handshakes per client IP
  io.use((socket: TSocket, next: (err?: Error) => void) => {
    const clientIp =
      socket.handshake?.address ||
      socket.conn?.remoteAddress ||
      'unknown';
    const verdict = connectionLimiter.check(`conn:${clientIp}`);
    if (!verdict.allowed) {
      next(new Error('Too many connections'));
      return;
    }
    next();
  });

  // Authenticate incoming Socket.IO handshakes fail-closed
  io.use((socket: TSocket, next: (err?: Error) => void) => {
    const currentEnv = envGetter();
    const configuredTokens = getConfiguredTokens(currentEnv);
    const trustIap = currentEnv.TRUST_IAP_HEADERS === 'true';

    if (configuredTokens.length === 0 && !trustIap) {
      next(new Error('Service authentication is not configured'));
      return;
    }

    const headers = (socket.handshake?.headers ?? {}) as Record<
      string,
      string | string[] | undefined
    >;

    if (hasValidIapIdentity(headers, currentEnv)) {
      next();
      return;
    }

    const authPayloadToken =
      typeof socket.handshake?.auth?.token === 'string'
        ? socket.handshake.auth.token.trim()
        : null;
    const rawAuthHeader = headers.authorization;
    const authHeaderStr = Array.isArray(rawAuthHeader)
      ? rawAuthHeader[0]
      : rawAuthHeader;
    const { token: bearerToken, malformed } = extractBearerToken(authHeaderStr);
    const rawApiKey = headers['x-api-key'];
    const apiKey =
      (Array.isArray(rawApiKey) ? rawApiKey[0] : rawApiKey)?.trim() || null;

    if (malformed && !authPayloadToken && !apiKey) {
      next(new Error('Unauthorized'));
      return;
    }

    const candidate = authPayloadToken || bearerToken || apiKey;
    if (!candidate || !timingSafeTokenMatches(candidate, configuredTokens)) {
      next(new Error('Unauthorized'));
      return;
    }

    next();
  });

  return { connectionLimiter, eventLimiter };
}

export function attachPerSocketEventRateLimit(
  socket: SocketLike,
  eventLimiter: SlidingWindowRateLimiter
): void {
  const clientIp =
    socket.handshake?.address || socket.conn?.remoteAddress || 'unknown';
  socket.use((_packet, next) => {
    const socketVerdict = eventLimiter.check(`sock:${socket.id}`);
    const ipVerdict = eventLimiter.check(`ip:${clientIp}`);
    if (!socketVerdict.allowed || !ipVerdict.allowed) {
      next(new Error('Rate limit exceeded'));
      return;
    }
    next();
  });
}

export const centralErrorHandler: ErrorRequestHandler = (
  err: { status?: number; statusCode?: number; type?: string; message?: string },
  _req: Request,
  res: Response,
  next: NextFunction
): void => {
  if (res.headersSent) {
    next(err);
    return;
  }

  if (
    err?.type === 'entity.too.large' ||
    err?.status === 413 ||
    err?.statusCode === 413
  ) {
    res.status(413).json({ error: 'Request payload too large' });
    return;
  }

  if (
    err instanceof SyntaxError ||
    err?.type === 'entity.parse.failed' ||
    err?.status === 400 ||
    err?.statusCode === 400
  ) {
    res.status(400).json({ error: 'Malformed request payload' });
    return;
  }

  console.error('Unhandled request error:', err?.message || 'Unknown error');
  res.status(500).json({ error: 'Internal server error' });
};
