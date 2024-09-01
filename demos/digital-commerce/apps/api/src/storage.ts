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
import {SaveOptions, Storage} from '@google-cloud/storage';


const storage = new Storage();

const BUCKET_NAME = process.env.STORAGE_BUCKET;

console.info(`Using bucket name: ${BUCKET_NAME}`)

if (!storage.bucket(BUCKET_NAME).exists) {
    storage.createBucket(BUCKET_NAME);
}

const bucket = storage.bucket(BUCKET_NAME);

const filOptions = (type: string) => {
    return {
        resumable: false,
        metadata: {contentType: type},
        validation: false,
    } as SaveOptions;
};

export const saveFile = async (
    id: string,
    job: string,
    type: string,
    dataUrl: string,
    extension: string,
    callback: (fulUri: string) => void
) => {
    try {
        const filName = `${job}-${id}-${Date.now()}.${extension}`.replace('_', '-');
        const filUri = `gs://${BUCKET_NAME}/${filName}`;
        const fil = bucket.file(filName);

        const base64EncodedString = dataUrl.replace(/^(.*);base64,/, '');
        const filBuf = Buffer.from(base64EncodedString, 'base64');
        const typeSemicolon = type.indexOf(';');
        if (typeSemicolon > 0) {
            type = type.substring(0, typeSemicolon);
        }
        await fil.save(filBuf, filOptions(type));
        callback(filUri);
    } catch (err) {
        console.error(err);
    }
};

export const deleteFile = async (filUri: string) => {
    try {
        const fil = bucket.file(filUri.substring(filUri.lastIndexOf('/') + 1));
        if (fil.exists) {
            await fil.delete();
        }
    } catch (err) {
        console.error(err);
    }
};
