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

import {GenerateContentResult} from '@google-cloud/vertexai';
import {Response} from 'express';
import {api} from 'model';

export const extractTextCandidates = (result: GenerateContentResult): string => {
    if (result.response.candidates) {
        return result.response.candidates[0].content.parts[0].text;
    } else {
        return 'no content';
    }
};

export const generateFailedDependencyResponse = (resp: Response) => {
    resp.status(424).send({code: 1001, error: 'failed to find session'} as api.ErrorResponse);
};
