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
import {
  generateKeyPairSync,
  KeyObject,
  sign as cryptoSign,
} from 'node:crypto';
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
  DEFAULT_MEDIA_JSON_BODY_LIMIT,
  DEFAULT_SOCKET_MAX_BUFFER_BYTES,
  getAllowedOrigins,
  IapJwk,
  IapJwksProvider,
  resolveBindHost,
  resolveJsonBodyLimit,
  resolveMediaJsonBodyLimit,
  resolveSocketClientIp,
  resolveSocketMaxBufferBytes,
  resolveTrustProxy,
  securityHeadersMiddleware,
  SlidingWindowRateLimiter,
  timingSafeTokenMatches,
  verifyIapJwtAssertion,
} from './security';

function buildTestExpressApp(
  env: NodeJS.ProcessEnv,
  rateLimiter?: SlidingWindowRateLimiter,
  iapJwksProvider?: IapJwksProvider
) {
  const envGetter = () => env;
  const app = express();
  app.disable('x-powered-by');
  app.set('trust proxy', resolveTrustProxy(env));
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

  app.get('/healthz', (_req: Request, res: Response) => {
    res.status(200).json({ status: 'ok' });
  });

  // Rate limit + Auth BEFORE any JSON parsing
  app.use(
    '/api',
    createApiRateLimitMiddleware(rateLimiter, envGetter),
    createApiAuthMiddleware(envGetter, iapJwksProvider)
  );

  const standardJson = json({ limit: resolveJsonBodyLimit(env) });
  const mediaJson = json({ limit: resolveMediaJsonBodyLimit(env) });

  app.post('/api/text', standardJson, (req: Request, res: Response) => {
    res.status(200).json({ echoed: req.body?.prompt ?? null });
  });

  app.post('/api/images', mediaJson, (req: Request, res: Response) => {
    res.status(200).json({ bytes: String(req.body?.image ?? '').length });
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

function makeSignedEs256Jwt(
  privateKey: KeyObject,
  header: Record<string, unknown>,
  payload: Record<string, unknown>
): string {
  const h = Buffer.from(JSON.stringify(header)).toString('base64url');
  const p = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const sig = cryptoSign('sha256', Buffer.from(`${h}.${p}`, 'ascii'), {
    key: privateKey,
    dsaEncoding: 'ieee-p1363',
  }).toString('base64url');
  return `${h}.${p}.${sig}`;
}

describe('Digital Commerce API Security Hardening', () => {
  it('enforces bounded standard/media JSON limits, Socket.IO limits, trust proxy, and bind host', () => {
    assert.equal(resolveJsonBodyLimit({}), DEFAULT_JSON_BODY_LIMIT);
    assert.equal(resolveJsonBodyLimit({ JSON_BODY_LIMIT: '512kb' }), '512kb');
    assert.equal(resolveJsonBodyLimit({ JSON_BODY_LIMIT: 'invalid!!' }), '1mb');
    assert.equal(resolveJsonBodyLimit({ JSON_BODY_LIMIT: '999999mb' }), '5mb');

    assert.equal(resolveMediaJsonBodyLimit({}), DEFAULT_MEDIA_JSON_BODY_LIMIT);
    assert.equal(
      resolveMediaJsonBodyLimit({ MEDIA_JSON_BODY_LIMIT: '999mb' }),
      '25mb'
    );

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

    assert.equal(resolveTrustProxy({}), false);
    assert.equal(resolveTrustProxy({ GAE_ENV: 'standard' }), 1);
    assert.equal(resolveTrustProxy({ TRUST_PROXY: '2' }), 2);
    assert.equal(resolveBindHost({}), '127.0.0.1');
    assert.equal(resolveBindHost({ NODE_ENV: 'production' }), '0.0.0.0');
    assert.equal(resolveBindHost({ GAE_ENV: 'flex' }), '0.0.0.0');

    // Socket client IP honors trust proxy right-most hop, not spoofed left-most XFF
    const ip = resolveSocketClientIp(
      {
        id: 's1',
        handshake: {
          address: '10.0.0.1',
          headers: { 'x-forwarded-for': '1.2.3.4, 198.51.100.77' },
        },
        use: () => undefined,
      },
      { TRUST_PROXY: '1' }
    );
    assert.equal(ip, '198.51.100.77');
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

  it('fails closed (503) on /api/* when auth is unconfigured or weak, while keeping /healthz public', async () => {
    const app = buildTestExpressApp({
      NODE_ENV: 'production',
      API_AUTH_TOKEN: 'too-short', // < 16 chars ignored
    });
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

  it('cryptographically verifies IAP ES256 JWTs and rejects spoofed IAP headers', async () => {
    const { publicKey, privateKey } = generateKeyPairSync('ec', {
      namedCurve: 'P-256',
    });
    const jwk: IapJwk = {
      ...(publicKey.export({ format: 'jwk' }) as IapJwk),
      kid: 'iap-key-1',
    };
    const jwksProvider: IapJwksProvider = async () => [jwk];
    const now = Math.floor(Date.now() / 1000);
    const audience = '/projects/123456/apps/demo-app';
    const env: NodeJS.ProcessEnv = {
      NODE_ENV: 'production',
      TRUST_IAP_HEADERS: 'true',
      IAP_AUDIENCE: audience,
      ALLOWED_ORIGINS: 'https://storefront.example.com',
    };

    // 1. Spoofed x-goog-authenticated-user-* headers without signed JWT -> rejected
    const spoofedOk = await verifyIapJwtAssertion(
      {
        'x-goog-authenticated-user-email': 'accounts.google.com:attacker@evil.com',
        'x-goog-authenticated-user-id': 'accounts.google.com:12345',
      },
      env,
      jwksProvider,
      now
    );
    assert.equal(spoofedOk, false);

    // 2. alg: none unsigned JWT -> rejected
    const algNoneJwt = `${Buffer.from(JSON.stringify({ alg: 'none', kid: 'iap-key-1' })).toString('base64url')}.${Buffer.from(
      JSON.stringify({
        iss: 'https://cloud.google.com/iap',
        aud: audience,
        email: 'user@example.com',
        sub: 'accounts.google.com:1',
        iat: now - 10,
        exp: now + 300,
      })
    ).toString('base64url')}.`;
    assert.equal(
      await verifyIapJwtAssertion(
        { 'x-goog-iap-jwt-assertion': algNoneJwt },
        env,
        jwksProvider,
        now
      ),
      false
    );

    // 3. Valid ES256 IAP JWT -> accepted
    const validJwt = makeSignedEs256Jwt(
      privateKey,
      { alg: 'ES256', kid: 'iap-key-1' },
      {
        iss: 'https://cloud.google.com/iap',
        aud: audience,
        email: 'user@example.com',
        sub: 'accounts.google.com:1',
        iat: now - 10,
        exp: now + 300,
      }
    );
    assert.equal(
      await verifyIapJwtAssertion(
        { 'x-goog-iap-jwt-assertion': validJwt },
        env,
        jwksProvider,
        now
      ),
      true
    );

    // 4. Wrong audience -> rejected
    assert.equal(
      await verifyIapJwtAssertion(
        { 'x-goog-iap-jwt-assertion': validJwt },
        { ...env, IAP_AUDIENCE: '/projects/999/apps/other' },
        jwksProvider,
        now
      ),
      false
    );

    // 5. Express route accepts valid IAP JWT and rejects spoofed headers
    const app = buildTestExpressApp(env, undefined, jwksProvider);
    await withServer(app, async (baseUrl) => {
      const spoofResp = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-goog-authenticated-user-email': 'accounts.google.com:attacker@evil.com',
          'x-goog-authenticated-user-id': 'accounts.google.com:1',
        },
        body: JSON.stringify({ prompt: 'spoof' }),
      });
      assert.equal(spoofResp.status, 401);

      const validResp = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-goog-iap-jwt-assertion': validJwt,
        },
        body: JSON.stringify({ prompt: 'via-iap' }),
      });
      assert.equal(validResp.status, 200);
      assert.deepEqual(await validResp.json(), { echoed: 'via-iap' });
    });
  });

  it('enforces auth before JSON parsing, strict CORS, per-route media limits, malformed JSON (400), generic 500, and rate limiting (429)', async () => {
    const limiter = new SlidingWindowRateLimiter({
      windowMs: 60_000,
      maxRequests: 7,
    });
    const env: NodeJS.ProcessEnv = {
      NODE_ENV: 'production',
      API_AUTH_TOKEN: 'super-secret-api-token',
      ALLOWED_ORIGINS: 'https://storefront.example.com',
      JSON_BODY_LIMIT: '1kb',
      MEDIA_JSON_BODY_LIMIT: '10kb',
    };
    const app = buildTestExpressApp(env, limiter);

    await withServer(app, async (baseUrl) => {
      // 1. Anonymous oversized request returns 401 (auth runs BEFORE body parser)
      const anonBig = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'x'.repeat(4096) }),
      });
      assert.equal(anonBig.status, 401);

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

      // 4. Oversized JSON payload on /api/text -> 413
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

      // 5. Larger media payload succeeds on authenticated /api/images
      const mediaOk = await fetch(`${baseUrl}/api/images`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer super-secret-api-token',
        },
        body: JSON.stringify({ image: 'a'.repeat(4096) }),
      });
      assert.equal(mediaOk.status, 200);
      assert.deepEqual(await mediaOk.json(), { bytes: 4096 });

      // 6. Malformed JSON -> 400
      const badJson = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer super-secret-api-token',
        },
        body: '{"prompt": broken',
      });
      assert.equal(badJson.status, 400);

      // 7. Unhandled server error -> generic 500 without stack trace or internal message
      const boom = await fetch(`${baseUrl}/api/boom`, {
        headers: { 'X-API-Key': 'super-secret-api-token' },
      });
      assert.equal(boom.status, 500);
      const boomText = await boom.text();
      assert.equal(boomText.includes('sensitive-internal-stack-secret'), false);

      // 8. 8th request to /api exceeds maxRequests=7 -> 429 Too Many Requests
      const rateLimited = await fetch(`${baseUrl}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer super-secret-api-token',
        },
        body: JSON.stringify({ prompt: 'eighth' }),
      });
      assert.equal(rateLimited.status, 429);
      assert.ok(rateLimited.headers.get('retry-after'));
    });
  });

  it('enforces Socket.IO handshake auth (fail-closed) and per-connection/per-event rate limits', async () => {
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

    const runHandshake = async (socket: any): Promise<Error | undefined> => {
      for (const mw of middlewares) {
        const err = await new Promise<Error | undefined>((resolve) => {
          mw(socket, (e?: Error) => resolve(e));
        });
        if (err) {
          return err;
        }
      }
      return undefined;
    };

    // Unconfigured auth -> fails closed
    const errUnconf = await runHandshake({
      handshake: { address: '127.0.0.1', auth: {}, headers: {} },
    });
    assert.ok(errUnconf instanceof Error);
    assert.match(errUnconf.message, /not configured/);

    // Configured auth, missing token -> Unauthorized
    currentEnv = { API_AUTH_TOKEN: 'socket-secret-token' };
    const errNoToken = await runHandshake({
      handshake: { address: '127.0.0.1', auth: {}, headers: {} },
    });
    assert.ok(errNoToken instanceof Error);
    assert.equal(errNoToken.message, 'Unauthorized');

    // Valid token via handshake.auth.token -> succeeds
    const errValid = await runHandshake({
      handshake: {
        address: '127.0.0.1',
        auth: { token: 'socket-secret-token' },
        headers: {},
      },
    });
    assert.equal(errValid, undefined);

    // 4th connection from same IP exceeds maxRequests=3 -> Too many connections
    const errConnLimit = await runHandshake({
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

  it('verifies main.ts and SPA clients wire hardened limits, post-auth body parsing, and no bundled VITE_API_AUTH_TOKEN', () => {
    const localMainPath = path.join(__dirname, 'main.ts');
    const mainPath = fs.existsSync(localMainPath)
      ? localMainPath
      : path.resolve(process.cwd(), 'apps/api/src/main.ts');
    const mainSource = fs.readFileSync(mainPath, 'utf8');
    assert.equal(mainSource.includes('50mb'), false);
    assert.equal(mainSource.includes('2e7'), false);
    assert.equal(/origin:\s*['"]\*['"]/.test(mainSource), false);
    assert.ok(mainSource.includes('app.use(securityHeadersMiddleware)'));
    assert.ok(mainSource.includes("app.set('trust proxy', resolveTrustProxy())"));
    assert.ok(mainSource.includes('resolveJsonBodyLimit()'));
    assert.ok(mainSource.includes('resolveMediaJsonBodyLimit()'));
    assert.ok(mainSource.includes('resolveSocketMaxBufferBytes()'));
    assert.ok(mainSource.includes('attachSocketSecurity(io)'));
    assert.ok(mainSource.includes('attachPerSocketEventRateLimit(socket, eventLimiter)'));
    assert.ok(mainSource.includes('app.use(centralErrorHandler)'));

    const authMountIdx = mainSource.indexOf(
      "app.use('/api', createApiRateLimitMiddleware(), createApiAuthMiddleware())"
    );
    const firstJsonParserIdx = mainSource.indexOf('const standardJsonParser');
    const firstApiRouteIdx = mainSource.indexOf("app.use('/api/registration'");
    assert.ok(authMountIdx > 0);
    assert.ok(firstJsonParserIdx > authMountIdx);
    assert.ok(firstApiRouteIdx > firstJsonParserIdx);

    // Ensure VITE_API_AUTH_TOKEN is never inlined in SPA source files
    const demoDir = path.resolve(path.dirname(mainPath), '../../demo/src');
    for (const rel of [
      'utils/WebClient.ts',
      'providers/BatchProvider.tsx',
      'providers/ConversationProvider.tsx',
    ]) {
      const p = path.join(demoDir, rel);
      if (fs.existsSync(p)) {
        const src = fs.readFileSync(p, 'utf8');
        assert.equal(
          src.includes('VITE_API_AUTH_TOKEN'),
          false,
          `Static secret VITE_API_AUTH_TOKEN must not appear in ${rel}`
        );
      }
    }
  });
});
