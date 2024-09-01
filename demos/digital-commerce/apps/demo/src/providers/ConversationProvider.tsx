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

import {ReactElement, useEffect, useState} from "react";
import {Interlocutor} from "../domain";
import {io, Socket} from "socket.io-client";
import {ConversationContext} from "../contexts";

const SOCKET_BASE = import.meta.env.VITE_SOCKET_URL_BASE

const getSocket = (): Socket => {
    return io(SOCKET_BASE);
}

const ConversationProvider = ({children}: { children: ReactElement | ReactElement[] }) => {
    const [socket] = useState<Socket>(getSocket);
    const [conversation, setConversation] = useState<Interlocutor[]>([]);

    useEffect(() => {
        // Register the socket event for the client and how to handle them.
        socket.once('connected', ({message}) => console.log(message));
        socket.on('voice:transcript', ({message}) => setConversation([...conversation, {
            role: 'user',
            value: message
        }]));
        socket.on('voice:response', (v) => {
            const r = JSON.parse(v) as { prompt: string; response: string };
            setConversation([...conversation, {role: 'system', value: r.response}]);
        });
        socket.on('voice:error', ({message}) => console.error(message));
    })

    return (
        <ConversationContext.Provider value={{conversation, setConversation, socket: socket}}>
            {children}
        </ConversationContext.Provider>
    )
}

export default ConversationProvider;