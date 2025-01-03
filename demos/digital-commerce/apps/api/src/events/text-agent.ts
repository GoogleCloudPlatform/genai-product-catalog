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

import { api } from "model";
import { Socket } from "socket.io";
import sessionManager from "../state";
import { extractTextCandidates } from "../utils";

export default (socket: Socket) => async ({sessionID, prompt, value}: api.ChatPromptRequest) => {
    const session = sessionManager.getSession(sessionID);

    const model = session.groundedModel;

    const chatPrompt = prompt + `\nProduct Data JSON: ${prompt}\nExample JSON output: {prompt: '${value}', response: 'Some generated response'} where the response value is in markdown format.`;

    model
        .generateContent({
            contents: [{role: 'user', parts: [{text: chatPrompt}]}],
        })
        .then((result) => {
            const value = extractTextCandidates(result);
            socket.emit('agent:response', value);
        });
}