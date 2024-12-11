// Copyright 2024 Google, LLC
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

import {GenerativeModel, VertexAI} from '@google-cloud/vertexai';
import {GenerativeConfig} from 'model';

import { config } from 'dotenv';
config()

const vertexAI = new VertexAI({
    project: process.env.GCP_PROJECT_ID,
    location: process.env.GCP_LOCATION,
});

export class GenerativeSession {
    public createdAt: number
    public config: GenerativeConfig;
    public model: GenerativeModel;
    public groundedModel: GenerativeModel;

    constructor(config: GenerativeConfig) {
        this.createdAt = Date.now()
        this.config = config;
        this.model = vertexAI.getGenerativeModel({
            model: config.modelName,
            systemInstruction: config.instructions,
            safetySettings: config.safetySettings,
            generationConfig: {
                maxOutputTokens: config.maxTokenCount,
                temperature: config.temperature,
                candidateCount: 1,
                topK: config.topK,
                topP: config.topP,
                responseMimeType: 'application/json',
            },
        });
        this.groundedModel = vertexAI.getGenerativeModel({
            model: config.modelName,
            systemInstruction: config.instructions,
            safetySettings: config.safetySettings,
            generationConfig: {
                maxOutputTokens: config.maxTokenCount,
                temperature: config.temperature,
                candidateCount: 1,
                topK: config.topK,
                topP: config.topP,
                responseMimeType: 'application/json',
            },
            tools: [
                {googleSearchRetrieval: {}}
            ]
        })
    }
}

class SessionState {
    state: Map<string, GenerativeSession>;

    constructor() {
        this.state = new Map<string, GenerativeSession>();
    }

    addSession(socketId: string, config: GenerativeConfig) {
        this.state.set(socketId, new GenerativeSession(config));
    }

    getSession(sessionID: string | undefined | null): GenerativeSession | undefined {
        return this.state.has(sessionID) ? this.state.get(sessionID) : undefined;
    }
}

const sessionManager = new SessionState();

// Check the session map every minute and delete any session over 20 minutes old
setInterval(function() {
    const checkTime = Date.now()
    sessionManager.state.forEach((value, key) => {
        const diffTime = checkTime - value.createdAt
        if (Math.floor(diffTime / 1000 / 60) % 60 > 19) {
            // Delete the session after 30 minutes
            sessionManager.state.delete(key)
        }
    })
}, 60 * 1000);

export default sessionManager;
