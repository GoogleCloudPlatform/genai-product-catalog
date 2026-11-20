// Copyright 2023 Google LLC
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

import { config } from 'dotenv';
import { createServer } from 'http';
import express, { Express, json } from 'express';
import cors from 'cors';

import { Server, Socket } from 'socket.io';

import defaults from './routes/defaults';
import registrationHandler from './routes/register';
import imageHandlers from './routes/images';
import textHandlers from './routes/text';
import videoHandlers from './routes/video';
import batchHandlers from './routes/batch';

import textAgent from './events/text-agent';
import voiceAgent from './events/voice-agent';
import batchStream from './events/batch-stream';
import {
  attachPerSocketEventRateLimit,
  attachSocketSecurity,
  centralErrorHandler,
  createApiAuthMiddleware,
  createApiRateLimitMiddleware,
  createExpressCorsOriginValidator,
  createSocketCorsOriginValidator,
  resolveBindHost,
  resolveJsonBodyLimit,
  resolveMediaJsonBodyLimit,
  resolveSocketMaxBufferBytes,
  resolveTrustProxy,
  securityHeadersMiddleware,
} from './security';

config();

export const app: Express = express();
app.disable('x-powered-by');
app.set('trust proxy', resolveTrustProxy());

app.use(securityHeadersMiddleware);

const corsOptions: cors.CorsOptions = {
  origin: createExpressCorsOriginValidator(),
  methods: ['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Authorization', 'Content-Type', 'X-API-Key'],
  credentials: true,
  optionsSuccessStatus: 200,
};

app.use(cors(corsOptions));

export const httpServer = createServer(app);

export const io = new Server(httpServer, {
  cors: {
    origin: createSocketCorsOriginValidator(),
    methods: ['GET', 'PUT', 'POST', 'DELETE'],
    credentials: true,
  },
  maxHttpBufferSize: resolveSocketMaxBufferBytes(),
});

const { eventLimiter } = attachSocketSecurity(io);

app.use('/', defaults);

// Enforce rate limiting and authentication BEFORE parsing any JSON request bodies.
app.use('/api', createApiRateLimitMiddleware(), createApiAuthMiddleware());

const standardJsonParser = json({ limit: resolveJsonBodyLimit() });
const mediaJsonParser = json({ limit: resolveMediaJsonBodyLimit() });

app.use('/api', standardJsonParser, defaults);
app.use('/api/registration', standardJsonParser, registrationHandler);
app.use('/api/text', standardJsonParser, textHandlers);
app.use('/api/batch', standardJsonParser, batchHandlers);
app.use('/api/images', mediaJsonParser, imageHandlers);
app.use('/api/video', mediaJsonParser, videoHandlers);

app.use(centralErrorHandler);

io.on('connection', (socket: Socket) => {
  attachPerSocketEventRateLimit(socket, eventLimiter);
  socket.on('agent:text', textAgent(socket));
  socket.on('agent:voice', voiceAgent(socket));
  socket.on('batch:request', batchStream(socket));
});

const port = Number(process.env.PORT) || 3000;
const host = resolveBindHost();
if (require.main === module) {
  httpServer.listen(port, host, () => {
    console.log(`[server]: Server is running at http://${host}:${port}`);
  });
}
