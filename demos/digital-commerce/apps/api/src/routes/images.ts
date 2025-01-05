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

import {Request, Response, Router} from 'express';
import {api} from 'model';
import sessionManager from '../state';
import {utils} from 'model';

import { generateFailedDependencyResponse, extractTextCandidates} from '../utils';
import { GenerativeContentBlob, InlineDataPart } from '@google/generative-ai';

const router = Router();

/**
 * Handle image to Category[]
 */
router.post('/', (req: Request, resp: Response) => {
    const imagePrompt = req.body as api.ImagePromptRequest;
    const sessionID = imagePrompt.sessionID;
    const generativeSession = sessionManager.getSession(sessionID);
    if (generativeSession) {
        const model = generativeSession.model;
        model
            .generateContent({
                contents: [
                    {
                        role: 'user',
                        parts: [
                            {text: imagePrompt.prompt},
                            ...imagePrompt.value.map(
                                (image) =>
                                    ({
                                        inlineData: {
                                            data: utils.stripBase64Prefix(image.base64),
                                            mimeType: image.type,
                                        } as GenerativeContentBlob,
                                    } as InlineDataPart)
                            ),
                        ],
                    },
                ],
            })
            .then((result) => {
                // console.log(`SUCCESS: ${extractTextCandidates(result)}`)
                resp.status(200).send(extractTextCandidates(result));
            });
    } else {
        console.error(`ERROR ...${JSON.stringify(resp)}`)
        generateFailedDependencyResponse(resp);
    }
});

export default router;
