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

import { GoogleAuth } from 'google-auth-library';
import { Socket } from 'socket.io';
import sessionManager from '../state';
import { extractTextCandidates } from '../utils';
import { BatchPromptRequest } from 'libs/model/src/lib/api';
import { BaseProduct, BatchProduct, Category, Image, Product } from 'model';
import axios from 'axios';
import { GenerativeModel } from '@google-cloud/vertexai';

const GCP_IMAGE_MODEL = process.env.GCP_IMAGE_MODEL;
const GCP_PROJECT_ID = process.env.GCP_PROJECT_ID;
const GCP_LOCATION = process.env.GCP_LOCATION;

interface SimpleProduct {
  language: string;
  name: string;
  category: string;
  description: string;
  seoHtmlHeader: string;
  attributeValues: { name: string; value: string | number | boolean }[];
}

interface SimpleImage {
  bytesBase64Encoded: string;
  mimeType: string;
}

interface ImageResponse {
  predictions: SimpleImage[];
}

const generate_image = (product: Product, socket: Socket) => {
  // TODO - reactor once the API is supported in main stream, until then use axios.
  // If you HAVE NOT been approved for imagen 3, you may need to change to an older model: imagegeneration@006

  const auth = new GoogleAuth();
  auth
    .getAccessToken()
    .then((token) => {
      const url = `https://${GCP_LOCATION}-aiplatform.googleapis.com/v1/projects/${GCP_PROJECT_ID}/locations/${GCP_LOCATION}/publishers/google/models/${GCP_IMAGE_MODEL}:predict`;
      const req_body = {
        instances: [
          {
            prompt: `Given the following JSON product details create an image of the product in an environment suitable for seeling the product on an e-commerce web site. Natural Lighting, High Contrast, 35mm, Vivid.\nProduct Details:\n${JSON.stringify(
              product
            )}`,
          },
        ],
        parameters: {
          sampleCount: 1,
        },
      };

      axios
        .post(url, req_body, {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Goog-User-Project': GCP_PROJECT_ID,
            'User-Agent': 'cloud-solutions/digital-commerce-deploy',
          },
        })
        .then((resp) => {
          const data = resp.data as ImageResponse;
          if (!product.images) {
            product.images = [];
          }
          product.images.push(
            ...data.predictions.map((s) => ({ base64: s.bytesBase64Encoded, type: s.mimeType } as Image))
          );
        })
        .catch((e) => {
          console.error(e);
          socket.emit('batch:error', { message: `Failed to generate image for: ${product.base.name}` });
        })
        .finally(() => socket.emit('batch:response', { message: product }));
    })
    .catch((e) => {
      console.error(e);
      socket.emit('batch:response', { message: product });
    });
};

const generate_product = ({
  model,
  socket,
  value,
  prompt,
  incrementor,
  count,
}: {
  model: GenerativeModel;
  socket: Socket;
  value: BatchProduct;
  prompt: string;
  incrementor: () => void;
  count: number;
}) => {
  model.generateContent({ contents: [{ role: 'user', parts: [{ text: prompt }] }] }).then((result) => {
    try {
      const resultText = extractTextCandidates(result);
      const obj = JSON.parse(resultText) as SimpleProduct;
      const product = {
        base: {
          language: obj.language,
          name: obj.name,
          description: obj.description,
          seoHtmlHeader: obj.seoHtmlHeader,
          attributeValues: obj.attributeValues,
        } as BaseProduct,
        category: { name: obj.category } as Category,
      } as Product;
      generate_image(product, socket);
      incrementor();
    } catch (e) {
      if (count < 3) {
        socket.emit('batch:warn', { message: `Retrying process for item: ${value.name}` });
        generate_product({
          model: model,
          socket: socket,
          value: value,
          prompt: prompt,
          incrementor: incrementor,
          count: count + 1,
        });
      } else {
        socket.emit('batch:error', { message: `Failed to process: ${value.name}` });
      }
    }
  });
};

export default (socket: Socket) =>
  async ({ sessionID, values }: BatchPromptRequest) => {
    const session = sessionManager.getSession(sessionID);
    const model = session.groundedModel;

    const exampleOutput = {
      language: 'EN-US',
      name: '',
      category: '',
      description: '',
      seoHtmlHeader: '',
      attributeValues: [{ name: '', value: '' }],
    } as SimpleProduct;

    const example = JSON.stringify(exampleOutput);

    const processRequestCount = values.length;
    let processed = 0;

    const incrementProcessed = (): void => {
      processed = processed + 1;
      if (processed === processRequestCount) {
        socket.emit('batch:complete', { message: `Processed: ${processed} of ${processRequestCount}` });
      }
    };

    values.forEach((value) => {
      const prompt =
        `Given the following product information follow the steps outlined below and produce a valid JSON response using the example output:
GTIN: ${value.gtin}
Product Name: ${value.name}
Short description: ${value.short_description}

- Find the top category and it's top 25 attributes and all matching values for this product, if there is not a matching value, do not include the attribute.
- The category hierarchy must be 4 levels deep, separated by ' > ' character as the category name.
- Write an enriched product description in markdown format for a retailers online catalog as the description.
- Write the HTML SEO description and keywords the product in plain text/html no Markdown as seoHtmlHeader.
- If the product is edible, include nutritional as additional attributeValues.

Example Output:
${example}
`.trim();
      generate_product({
        model: model,
        socket: socket,
        value: value,
        prompt: prompt,
        incrementor: incrementProcessed,
        count: 0,
      });
    });
  };
