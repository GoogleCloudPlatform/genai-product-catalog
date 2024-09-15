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

import {ReactElement, useContext, useEffect, useState} from "react";
import {io, Socket} from "socket.io-client";
import { BatchContext, ConversationContext } from "../contexts";
import { Product } from "model";

const SOCKET_BASE = import.meta.env.VITE_SOCKET_URL_BASE

const getSocket = (): Socket => {
    return io(SOCKET_BASE);
}

const initialState = () => []

const BatchProvider = ({children}: { children: ReactElement | ReactElement[] }) => {
    const {socket} = useContext(ConversationContext);
    const [products, setProducts] = useState<Product[]>(initialState)

    socket.once('connected', ({message}) => console.log(message));
    socket.on('batch:response', ({message}) => {
        setProducts([...products, message])
    });

    return(
        <BatchContext.Provider value={{socket, products, setProducts}}>
            {children}
        </BatchContext.Provider>
    )

};

export default BatchProvider;