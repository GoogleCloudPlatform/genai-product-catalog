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

import speech from '@google-cloud/speech';
import {Request, Response, Router} from 'express';
import {api} from 'model';
import sessionManager from '../state';
import {extractTextCandidates, generateFailedDependencyResponse} from '../utils';
import {saveFile} from '../storage';

const router = Router();

const speechClient = new speech.SpeechClient();
export const AUDIO_EXTENSION = 'webm';

router.post('/', async (req: Request, resp: Response) => {
    const audioPrompt = req.body as api.AudioPromptRequest;
    const {model} = sessionManager.getSession(audioPrompt.sessionID);
    if (model) {
        const handleFile = async (filUri: string) => {
            const [speechResponse] = await speechClient.recognize({
                config: {
                    encoding: 'WEBM_OPUS',
                    sampleRateHertz: 48000,
                    languageCode: 'en-US',
                },
                audio: {uri: filUri},
            });

            if (speechResponse && speechResponse.results) {
                const transcription = speechResponse.results
                    .map((result) =>
                        result.alternatives && result.alternatives.length > 0 ? result.alternatives[0].transcript : ''
                    )
                    .join('\n');

                const prompt = transcription + `\nUse the following Product Data for additional information: ${JSON.stringify(audioPrompt.prompt)}`;

                model
                    .generateContent({
                        contents: [{role: 'user', parts: [{text: prompt}]}],
                    })
                    .then((result) => {
                        resp.status(200).send({
                            transcript: transcription,
                            value: extractTextCandidates(result)
                        } as api.AudioResponse);
                    });
            }
        };

        await saveFile(
            audioPrompt.sessionID,
            'voice:transcript',
            audioPrompt.type,
            audioPrompt.value,
            AUDIO_EXTENSION,
            handleFile
        );
    } else {
        generateFailedDependencyResponse(resp);
    }
});

export default router;
