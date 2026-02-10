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
import {GenerateContentResponse} from '@google/genai'
import {Response} from 'express';
import {api} from 'model';

export const extractTextCandidates = (result: GenerateContentResponse, raw: boolean = false): string => {
    if (result) {
        let text = '';
        let partCount = 0;
        if (result.candidates) {
            result.candidates.forEach(candidate => {
                if (candidate.content && candidate.content.parts) {
                    candidate.content.parts.forEach(part => {
                        if (part.text) {
                            text += part.text;
                            partCount++;
                        }
                    });
                }
            });
        }

        if (partCount > 1) {
            console.log(`Found ${partCount} parts in response candidates.`);
        }

        if (text.includes("```json")) {
            text = text.replace("```json", "").replace("```", "");
        }

        // Clean up any non-printable characters and extra backslashes.
        text = text.trim().replace(/\\(?!["\\/bfnrt])/g, "\\\\");

        if (raw) {
            return text;
        }

        try {
            // Test if the cleaned text is valid JSON
            JSON.parse(text);
            // If it is, return it directly as the response property
            return JSON.stringify({ response: text });
        } catch (e) {
            // If not, it's likely a plain string, so wrap it.
            return JSON.stringify({ response: text });
        }
    } else {
        return raw ? '' : JSON.stringify({ response: 'no content' });
    }
};

export const generateFailedDependencyResponse = (resp: Response) => {
    resp.status(424).send({code: 1001, error: 'failed to find session'} as api.ErrorResponse);
};
