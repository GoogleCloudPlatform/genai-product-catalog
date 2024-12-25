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
import {extractTextCandidates, generateFailedDependencyResponse} from '../utils';
import {deleteFile, saveFile} from '../storage';
import {Category} from 'model';

const VIDEO_FILE_EXTENSION = 'mp4';

const router = Router();

router.post('/', async (req: Request, resp: Response) => {
    const videoRequest = req.body as api.VideoPromptRequest;

    const {model, groundedModel} = sessionManager.getSession(videoRequest.sessionID);

    if (model) {
        const handleFile = async (filUri: string) => {
            const fileData = {mimeType: videoRequest.type, fileUri: filUri};
            model
                .generateContent({
                    contents: [{role: 'user', parts: [{text: videoRequest.prompt}, {fileData: fileData}]}],
                })
                .then((result) => {
                    const videoResultText = extractTextCandidates(result) as string;

                    console.log(videoResultText);

                    groundedModel.generateContent({
                        contents: [{
                            role: 'user',
                            parts: [{text: videoRequest.categoryPrompt}, {text: `Product Information: ${videoResultText}`}]
                        }]
                    }).then(categoryResult => {
                        const categoryResponeText = extractTextCandidates(categoryResult);

                        console.log(categoryResponeText)

                        try {
                            const category = JSON.parse(categoryResponeText) as Category[];

                            const productCategoryAttributes = category[0].attributes.map(a => new Object({
                                name: a.name,
                                value: ''
                            }))

                            const productDetailPrompt = videoRequest.productDetailPrompt
                                .replace('${category_attributes}', JSON.stringify(category[0].attributes))
                                .replace('${product_attribute_value_model}', JSON.stringify(productCategoryAttributes));

                            console.log(productDetailPrompt)

                            groundedModel.generateContent({
                                contents: [{role: 'user', parts: [{text: productDetailPrompt}]}]
                            }).then((productResult) => {
                                // Send the final product
                                resp.status(200).send(extractTextCandidates(productResult))
                            }).catch(productErr => resp.status(400).send({error: productErr}));

                        } catch (marshallErr) {
                            console.log(`Marshall Error: ${marshallErr}`)
                            resp.status(400).send({error: marshallErr});
                        }

                    }).catch(categoryErr => resp.status(400).send({error: categoryErr}));
                })
                .catch((err) => resp.status(400).send({error: err}))
                .finally(() => {
                    deleteFile(filUri);
                });
        };
        await saveFile(
            videoRequest.sessionID,
            'video:request',
            videoRequest.type,
            videoRequest.value,
            VIDEO_FILE_EXTENSION,
            handleFile
        );
    } else {
        generateFailedDependencyResponse(resp);
    }
});

export default router;
