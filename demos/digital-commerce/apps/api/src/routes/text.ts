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
// limitations under the.

import {Request, Response, Router} from 'express';
import {api} from 'model';
import sessionManager from '../state';
import {extractTextCandidates, generateFailedDependencyResponse} from '../utils';

const router = Router();

router.post('/', (req: Request, resp: Response) => {
    const {sessionID, prompt} = req.body as api.TextPromptRequest;
    const {ai, config, groundedModelParams} = sessionManager.getSession(sessionID);
    if (ai) {
        ai.models
            .generateContent({
                model: config.modelName,
                contents: [{role: 'user', parts: [{text: prompt}]}],
                config: groundedModelParams
            })
            .then((result) => {
                resp.status(200).send(extractTextCandidates(result));
            })
            .catch((e) => {
                console.error(e);
                resp.status(400).send({error: 'Failed to generate content'} as api.ErrorResponse);
            });
    } else {
        generateFailedDependencyResponse(resp);
    }
});

export default router;
