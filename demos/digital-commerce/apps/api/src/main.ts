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

import { config } from 'dotenv'
import {createServer} from 'http';
import express, {Express, json} from 'express';
import cors from 'cors';

import {Server, Socket} from 'socket.io';

import defaults from './routes/defaults';
import registrationHandler from './routes/register';
import imageHandlers from './routes/images';
import textHandlers from './routes/text';
import videoHandlers from './routes/video';
import batchHandlers from './routes/batch';

import voiceStream from './events/voice-prompt';
import batchStream from './events/batch-stream';


config()

const app: Express = express();

app.use(json({limit: '50mb'}));
const corsOptions = {
    origin: "*",
    methods: ["GET", "PUT", "POST", "DELETE"],
    optionsSuccessStatus: 200
}

app.use(cors(corsOptions));

const httpServer = createServer(app);

const io = new Server(httpServer, {
    cors: {origin: '*', methods: ["GET", "PUT", "POST", "DELETE"]},
    maxHttpBufferSize: 2e7,
});

app.use('/', defaults);

app.use('/api', defaults);

app.use('/api/registration', registrationHandler);
app.use('/api/text', textHandlers);
app.use('/api/images', imageHandlers);
app.use('/api/video', videoHandlers);
app.use('/api/batch', batchHandlers);


io.on('connection', (socket: Socket) => {
    console.log(`Connected: ${socket.id}`);
    socket.on('voice:request', voiceStream(socket));
    socket.on('batch:request', batchStream(socket));
});

const port = process.env.PORT || 3000;
httpServer.listen(port, () => {
    console.log(`[server]: Server is running at http://localhost:${port}`);
});
