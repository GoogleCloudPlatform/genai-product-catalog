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

import {Firestore} from '@google-cloud/firestore';
import {Request, Response, Router} from 'express';
import {api} from 'model';
import {v4 as uuidv4} from 'uuid';
import sessionManager from '../state';
import {Config, GenerativeConfig} from 'model';

const router = Router();


const DATABASE_ID = process.env.FIRESTORE_DB_ID;
const COLLECTION = process.env.FIRESTORE_COLLECTION;

const firestoreSettings = {
    databaseId: DATABASE_ID,
} as FirebaseFirestore.Settings;

interface PersistentConfig {
    id: string;
    date: number;
    config: Config;
}

const persistToFirestore = (id: string, config: Config): Promise<FirebaseFirestore.WriteResult> => {
    if (firestoreSettings.databaseId) {
        const db = new Firestore(firestoreSettings);
        const persistentConfig = {id: id, date: Date.now(), config: config} as PersistentConfig;
        console.log("Yep, still here " + firestoreSettings.databaseId)
        const docRef = db.collection(COLLECTION).doc(persistentConfig.id);
        return docRef.set(persistentConfig, {merge: true});
    } else {
        console.log("configuration not persisted to firestore")
    }
};

router.post('/', (req: Request, resp: Response) => {
    const registrationRequest = req.body as api.ConfigurationRequest;

    const sessionID = registrationRequest.sessionID;
    const value = registrationRequest.config;

    const activeId = sessionID !== undefined && sessionID !== null && sessionID.trim().length > 0 ? sessionID : uuidv4();

    const existingConfig = sessionManager.getSession(sessionID);

    

    if (!existingConfig) {
        
        const configCopy = {...value};
        configCopy.generativeConfig.genAIToken = 'x'.repeat(8);
        persistToFirestore(activeId, configCopy)
            .then(() => {
                sessionManager.addSession(activeId, value.generativeConfig);
                console.log("Yep, still here")
                resp.status(201).send({sessionID: activeId, message: 'created'} as api.ConfigurationResponse);
            })
            .catch((err) => resp.status(400).send({error: err} as api.ErrorResponse));
    } else {
        const mergedConfig = {...existingConfig.config, ...value.generativeConfig} as GenerativeConfig;
        sessionManager.addSession(activeId, mergedConfig);
        resp.status(202).send({sessionID: activeId, message: 'updated'} as api.ConfigurationResponse);
    }
});

export default router;
