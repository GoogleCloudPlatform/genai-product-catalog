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

import {Socket} from 'socket.io';
import {deleteFile, saveFile} from '../storage';
import sessionManager from '../state';

import speech from '@google-cloud/speech';
import {extractTextCandidates} from '../utils';
import {api} from 'model';

const speechClient = new speech.SpeechClient();
export const AUDIO_EXTENSION = 'webm';

export default (socket: Socket) =>
    async ({sessionID, type, prompt, value}: api.AudioPromptRequest) => {
        const session = sessionManager.getSession(sessionID);

        const model = session.groundedModel;

        const handleFile = async (filUri: string) => {
            console.log(`file handle ${filUri}`);
            const [resp] = await speechClient.recognize({
                config: {
                    encoding: 'WEBM_OPUS',
                    sampleRateHertz: 48000,
                    languageCode: 'en-US',
                    enableAutomaticPunctuation: true
                },
                audio: {uri: filUri},
            });

            if (resp && resp.results) {
                const transcription = resp.results
                    .map((result) =>
                        result.alternatives && result.alternatives.length > 0 ? result.alternatives[0].transcript : ''
                    )
                    .join('\n');

                socket.emit('voice:transcript', {
                    message: transcription,
                });

                const audioPrompt = transcription + `\nProduct Data JSON: ${prompt}\nExample JSON output: {prompt: '${transcription}', response: 'Some generated response'} where the response value is in markdown format.`;

                model
                    .generateContent({
                        contents: [{role: 'user', parts: [{text: audioPrompt}]}],
                    })
                    .then((result) => {
                        const value = extractTextCandidates(result);
                        socket.emit('voice:response', value);
                    })
                    .finally(() => {
                        deleteFile(filUri);
                    });
            }
        };

        if (model) {
            await saveFile(sessionID, 'voice-transcript', type, value, AUDIO_EXTENSION, handleFile);
        } else {
            socket.emit('voice:error', {
                message: 'invalid session',
            });
        }
    };
