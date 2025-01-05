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


import {Response} from 'express';
import {api} from 'model';
import { GenerateContentResult } from '@google/generative-ai';

export const extractTextCandidates = (result: GenerateContentResult): string => {
    if (result.response.candidates) {
        let text = result.response.candidates[0].content.parts[0].text;

        if (text.startsWith("[") && text.endsWith("}")) {
            text = text.substring(0, text.length - 1)
        }

        text = text.replace(/\\(?!["\\/bfnrt])/g, "\\\\");

        try {
            JSON.parse(text);
            return text;
        } catch (e) {
            console.log(`invalid JSON response from Gemini ${e}`)
            return "[{name='error'}]"
        }


    } else {
        return 'no content';
    }
};

export const generateFailedDependencyResponse = (resp: Response) => {
    resp.status(424).send({code: 1001, error: 'failed to find session'} as api.ErrorResponse);
};
