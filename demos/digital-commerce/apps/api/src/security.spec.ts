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

import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createServer, Server as HttpServer } from 'node:http';
import type { AddressInfo } from 'node:net';
import path from 'node:path';
import { describe, it } from 'node:test';
import cors from 'cors';
import express, { json, Request, Response } from 'express';

import {
  attachPerSocketEventRateLimit,
  attachSocketSecurity,
  centralErrorHandler,
  createApiAuthMiddleware,
  createApiRateLimitMiddleware,
  createExpressCorsOriginValidator,
  createSocketCorsOriginValidator,
  DEFAULT_JSON_BODY_LIMIT,
  DEFAULT_SOCKET_MAX_BUFFER_BYTES,
  getAllowedOrigins,
  resolveJsonBodyLimit,
  resolveSocketMaxBufferBytes,
  securityHeadersMiddleware,
  SlidingWindowRateLimiter,
  timingSafeTokenMatches,
} from './security';

function buildTestExpressApp(
  env: NodeJS.ProcessEnv,
  rateLimiter?: SlidingWindowRateLimiter
) {
  const envGetter = () => env;
  const app = express();
  app.disable('x-powered-by');
  app.use(securityHeadersMiddleware);
  app.use(
    cors({
      origin: createExpressCorsOriginValidator(envGetter),
      methods: ['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Authorization', 'Content-Type', 'X-API-Key'],
      credentials: true,
      optionsSuccessStatus: 200,
    })
  );
  app.use(json({ limit: resolveJsonBodyLimit(env) }));

  app.get('/healthz', (_req: Request, res: Response) => {
    res.status(200).json({ status: 'ok' });
  });

  app.use(
    '/api',
    createApiRateLimitMiddleware(rateLimiter, envGetter),
    createApiAuthMiddleware(envGetter)
  );

  app.post('/api/text', (req: Request, res: Response) => {
    res.status(200).json({ echoed: req.body?.prompt ?? null });
  });

  app.get('/api/boom', () => {
    throw new Error('sensitive-internal-stack-secret');
  });

  app.use(centralErrorHandler);
  return app;
}

async function withServer(
  app: ReturnType<typeof express>,
  fn: (baseUrl: string) => Promise<void>
): Promise<void> {
  const server: HttpServer = createServer(app);
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  try {
    const addr = server.address() as AddressInfo;
    await fn(`http://127.0.0.1:${addr.port}`);
  } finally {
    await new Promise<void>((resolve, reject) =>
      server.close((err) => (err ? reject(err) : resolve()))
    );
  }
}

describe('Digital Commerce API Security Hardening', () => {
  it('enforces 1mb default JSON body limit and 1 MiB Socket.IO buffer limit', () => {
    assert.equal(resolveJsonBodyLimit({}), DEFAULT_JSON_BODY_LIMIT);
    assert.equal(resolveJsonBodyLimit({ JSON_BODY_LIMIT: '512kb' }), '512kb');
    assert.equal(resolveJsonBodyLimit({ JSON_BODY_LIMIT: 'invalid!!' }), '1mb');

    assert.equal(
      resolveSocketMaxBufferBytes({}),
      DEFAULT_SOCKET_MAX_BUFFER_BYTES
    );
    assert.equal(
      resolveSocketMaxBufferBytes({ SOCKET_MAX_BUFFER_BYTES: '-5' }),
      DEFAULT_SOCKET_MAX_BUFFER_BYTES
    );
    assert.equal(
      resolveSocketMaxBufferBytes({ SOCKET_MAX_BUFFER_BYTES: '999999999' }),
      10 * 1_048_576
    );
  });

  it('rejects wildcard CORS origins and fails closed in production without ALLOWED_ORIGINS', () => {
    const prodDefault = getAllowedOrigins({ NODE_ENV: 'production' });
    assert.equal(prodDefault.size, 0);

    const wildcardAttempt = getAllowedOrigins({
      NODE_ENV: 'production',
      ALLOWED_ORIGINS: '*,https://shop.example.com,ftp://bad.example.com',
    });
    assert.deepEqual([...wildcardAttempt], ['https://shop.example.com']);
    assert.equal(wildcardAttempt.has('*'), false);

    const socketOriginValidator = createSocketCorsOriginValidator(() => ({
      NODE_ENV: 'production',
      ALLOWED_ORIGINS: 'https://shop.example.com',
    }));

    let evilErr: unknown = null;
    socketOriginValidator('https://evil.example.com', (err) => {
      evilErr = err;
    });
    assert.ok(evilErr instanceof Error);

    let allowedOk = false;
    socketOriginValidator('https://shop.example.com', (err, allow) => {
      assert.equal(err, null);
      allowedOk = Boolean(allow);
    });
    assert.equal(allowedOk, true);
  });

  it('uses constant-time token comparison without leaking length errors', () => {
    assert.equal(timingSafeTokenMatches('', ['secret']), false);
    assert.equal(timingSafeTokenMatches('short', ['much-longer-secret']), false);
    assert.equal(
      timingSafeTokenMatches('valid-token-123', ['other', 'valid-token-123']),
      true
    );
  });

  it('fails closed (503) on /api/* when auth is unconfigured while keeping /healthz public with security headers', async () => {
    const app = buildTestExpressApp({ NODE_ENV: 'production' });
    await withServer(app, async (baseUrl) => {
      const health = await fetch(`${baseUrl}/healthz`);
      assert.equal(health.status, 200);
      assert.equal(health.headers.get('x-content-type-options'), 'nosniff');
      assert.equal(health.headers.get('x-frame-options'), 'DENY');
      assert.equal(health.headers.get('referrer-policy'), 'no-referrer');
      assert.match(
        health.headers.get('content-security-policy') ?? '',
        /frame-ancestors 'none'/
      );
      assert.equal(health.headers.get('x-powered-by'), null);

      const unconf = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'hello' }),
      });
      assert.equal(unconf.status, 503);
    });
  });

  it('enforces Bearer/API-key auth, strict CORS, 1mb body limit (413), malformed JSON (400), generic 500, and rate limiting (429)', async () => {
    const limiter = new SlidingWindowRateLimiter({
      windowMs: 60_000,
      maxRequests: 4,
    });
    const env: NodeJS.ProcessEnv = {
      NODE_ENV: 'production',
      API_AUTH_TOKEN: 'super-secret-api-token',
      ALLOWED_ORIGINS: 'https://storefront.example.com',
      JSON_BODY_LIMIT: '1kb',
    };
    const app = buildTestExpressApp(env, limiter);

    await withServer(app, async (baseUrl) => {
      // 1. Anonymous request -> 401
      const anon = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'hi' }),
      });
      assert.equal(anon.status, 401);

      // 2. Untrusted Origin -> 403 and no Access-Control-Allow-Origin
      const evilOrigin = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Origin: 'https://attacker.example.com',
          Authorization: 'Bearer super-secret-api-token',
        },
        body: JSON.stringify({ prompt: 'hi' }),
      });
      assert.equal(evilOrigin.status, 403);
      assert.equal(
        evilOrigin.headers.get('access-control-allow-origin'),
        null
      );

      // 3. Trusted Origin + valid Bearer token -> 200
      const ok = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Origin: 'https://storefront.example.com',
          Authorization: 'Bearer super-secret-api-token',
        },
        body: JSON.stringify({ prompt: 'catalog query' }),
      });
      assert.equal(ok.status, 200);
      assert.equal(
        ok.headers.get('access-control-allow-origin'),
        'https://storefront.example.com'
      );
      assert.deepEqual(await ok.json(), { echoed: 'catalog query' });

      // 4. Oversized JSON payload -> 413 (parsed before /api limiter)
      const largeBody = JSON.stringify({ prompt: 'x'.repeat(4096) });
      const tooLarge = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer super-secret-api-token',
        },
        body: largeBody,
      });
      assert.equal(tooLarge.status, 413);

      // 5. Malformed JSON -> 400
      const badJson = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer super-secret-api-token',
        },
        body: '{"prompt": broken',
      });
      assert.equal(badJson.status, 400);

      // 6. Unhandled server error -> generic 500 without stack trace or internal message
      const boom = await fetch(`${baseUrl}/api/boom`, {
        headers: { 'X-API-Key': 'super-secret-api-token' },
      });
      assert.equal(boom.status, 500);
      const boomText = await boom.text();
      assert.equal(boomText.includes('sensitive-internal-stack-secret'), false);

      // 7. 5th request to /api exceeds maxRequests=4 -> 429 Too Many Requests
      const rateLimited = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer super-secret-api-token',
        },
        body: JSON.stringify({ prompt: 'fifth' }),
      });
      assert.equal(rateLimited.status, 429);
      assert.ok(rateLimited.headers.get('retry-after'));
    });
  });

  it('enforces Socket.IO handshake auth (fail-closed) and per-connection/per-event rate limits', () => {
    const middlewares: Array<(socket: any, next: (err?: Error) => void) => void> = [];
    const fakeIo = {
      use(fn: (socket: any, next: (err?: Error) => void) => void) {
        middlewares.push(fn);
      },
    } as any;

    let currentEnv: NodeJS.ProcessEnv = {};
    const connLimiter = new SlidingWindowRateLimiter({
      windowMs: 60_000,
      maxRequests: 3,
    });
    const eventLimiter = new SlidingWindowRateLimiter({
      windowMs: 60_000,
      maxRequests: 2,
    });

    attachSocketSecurity(fakeIo, {
      envGetter: () => currentEnv,
      connectionLimiter: connLimiter,
      eventLimiter,
    });

    const runHandshake = (socket: any): Error | undefined => {
      let capturedErr: Error | undefined;
      for (const mw of middlewares) {
        let progressed = false;
        mw(socket, (err?: Error) => {
          if (err) {
            capturedErr = err;
          } else {
            progressed = true;
          }
        });
        if (capturedErr || !progressed) {
          break;
        }
      }
      return capturedErr;
    };

    // Unconfigured auth -> fails closed
    const errUnconf = runHandshake({
      handshake: { address: '127.0.0.1', auth: {}, headers: {} },
    });
    assert.ok(errUnconf instanceof Error);
    assert.match(errUnconf.message, /not configured/);

    // Configured auth, missing token -> Unauthorized
    currentEnv = { API_AUTH_TOKEN: 'socket-secret-token' };
    const errNoToken = runHandshake({
      handshake: { address: '127.0.0.1', auth: {}, headers: {} },
    });
    assert.ok(errNoToken instanceof Error);
    assert.equal(errNoToken.message, 'Unauthorized');

    // Valid token via handshake.auth.token -> succeeds
    const errValid = runHandshake({
      handshake: {
        address: '127.0.0.1',
        auth: { token: 'socket-secret-token' },
        headers: {},
      },
    });
    assert.equal(errValid, undefined);

    // 4th connection from same IP exceeds maxRequests=3 -> Too many connections
    const errConnLimit = runHandshake({
      handshake: {
        address: '127.0.0.1',
        auth: { token: 'socket-secret-token' },
        headers: {},
      },
    });
    assert.ok(errConnLimit instanceof Error);
    assert.equal(errConnLimit.message, 'Too many connections');

    // Per-socket event rate limit check
    let packetMw: ((packet: any[], next: (err?: Error) => void) => void) | null = null;
    const fakeSocket = {
      id: 'sock-1',
      handshake: { address: '127.0.0.2' },
      use(fn: (packet: any[], next: (err?: Error) => void) => void) {
        packetMw = fn;
      },
    } as any;
    attachPerSocketEventRateLimit(fakeSocket, eventLimiter);
    assert.ok(packetMw);

    const runEvent = (): Error | undefined => {
      let eventErr: Error | undefined;
      packetMw!(['agent:text', {}], (err?: Error) => {
        eventErr = err;
      });
      return eventErr;
    };
    assert.equal(runEvent(), undefined);
    assert.equal(runEvent(), undefined);
    const thirdEventErr = runEvent();
    assert.ok(thirdEventErr instanceof Error);
    assert.equal(thirdEventErr.message, 'Rate limit exceeded');
  });

  it('verifies main.ts entrypoint wires security headers, strict CORS, 1mb limits, rate limit, auth, and error handler', () => {
    const localMainPath = path.join(__dirname, 'main.ts');
    const mainPath = fs.existsSync(localMainPath)
      ? localMainPath
      : path.resolve(process.cwd(), 'apps/api/src/main.ts');
    const mainSource = fs.readFileSync(mainPath, 'utf8');
    assert.equal(mainSource.includes('50mb'), false);
    assert.equal(mainSource.includes('2e7'), false);
    assert.equal(/origin:\s*['"]\*['"]/.test(mainSource), false);
    assert.ok(mainSource.includes('app.use(securityHeadersMiddleware)'));
    assert.ok(mainSource.includes('resolveJsonBodyLimit()'));
    assert.ok(mainSource.includes('resolveSocketMaxBufferBytes()'));
    assert.ok(mainSource.includes('attachSocketSecurity(io)'));
    assert.ok(mainSource.includes('attachPerSocketEventRateLimit(socket, eventLimiter)'));
    assert.ok(mainSource.includes('app.use(centralErrorHandler)'));

    const authMountIdx = mainSource.indexOf(
      "app.use('/api', createApiRateLimitMiddleware(), createApiAuthMiddleware())"
    );
    const firstApiRouteIdx = mainSource.indexOf("app.use('/api/registration'");
    assert.ok(authMountIdx > 0);
    assert.ok(firstApiRouteIdx > authMountIdx);
  });
});
