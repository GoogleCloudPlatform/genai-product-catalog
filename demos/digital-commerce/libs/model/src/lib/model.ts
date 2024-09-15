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

import { DEFAULT_LANGUAGE } from './languages';

export interface Attribute {
  name: string;
  description: string;
  valueRange: string[];
}

export interface Category {
  name: string;
  attributes?: Attribute[];
}

export interface ProductAttributeValue {
  name: string;
  value: string;
}

export interface Image {
  uri?: string;
  base64: string;
  type: string;
}

export interface BatchProduct {
  id?: number,
  isNew?: boolean,
  gtin?: string, 
  name: string, 
  short_description: string,
}

export interface BaseProduct {
  language: string;
  name: string;
  description: string;
  seoHtmlHeader: string;
  attributeValues: ProductAttributeValue[];
}

export interface Product {
  base: BaseProduct;
  category: Category;
  images: Image[];
  alternatives?: Product[];
}

export enum HarmCategory {
  /** The harm category is unspecified. */
  HARM_CATEGORY_UNSPECIFIED = "HARM_CATEGORY_UNSPECIFIED",
  /** The harm category is hate speech. */
  HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH",
  /** The harm category is dangerous content. */
  HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT",
  /** The harm category is harassment. */
  HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT",
  /** The harm category is sexually explicit content. */
  HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
}
/**
* Probability based thresholds levels for blocking.
*/
export enum HarmBlockThreshold {
  /** Unspecified harm block threshold. */
  HARM_BLOCK_THRESHOLD_UNSPECIFIED = "HARM_BLOCK_THRESHOLD_UNSPECIFIED",
  /** Block low threshold and above (i.e. block more). */
  BLOCK_LOW_AND_ABOVE = "BLOCK_LOW_AND_ABOVE",
  /** Block medium threshold and above. */
  BLOCK_MEDIUM_AND_ABOVE = "BLOCK_MEDIUM_AND_ABOVE",
  /** Block only high threshold (i.e. block less). */
  BLOCK_ONLY_HIGH = "BLOCK_ONLY_HIGH",
  /** Block none. */
  BLOCK_NONE = "BLOCK_NONE"
}

export interface SafetySetting {
  category: HarmCategory
  threshold: HarmBlockThreshold
}

export interface GenerativeConfig {
  modelName: string
  genAIToken: string
  instructions: string
  temperature: number
  topP: number
  topK: number
  maxTokenCount: number
  safetySettings: SafetySetting[]
}

export interface Config {
  customerName: string
  engineerLdap: string
  defaultLanguage: string
  supportedLanguages: string[]
  promptDetectCategories: string
  promptExtractProductDetail: string
  promptTranslateProductDetail: string
  promptVideo: string
  generativeConfig: GenerativeConfig
}

export const NewProduct = (language: string = DEFAULT_LANGUAGE): Product => {
  return {
    base: {
      language: language,
      name: '',
      description: '',
      seoHtmlHeader: '',
      attributeValues: new Array<ProductAttributeValue>(),
    } as BaseProduct,
    images: new Array<Image>(),
    alternatives: new Array<Product>(),
  } as Product;
};

export const ProductAsJsonString = () => {
  return JSON.stringify(NewProduct());
};

export const NewGenerativeConfig = (instructions: string) => {
  return {
    modelName: 'gemini-1.5-flash',
    genAIToken: '',
    instructions: instructions,
    temperature: 0.2,
    topP: 0.94,
    topK: 32,
    maxTokenCount: 8192,
    safetySettings: [
      {
        category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold: HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
      },
      {
        category: HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold: HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
      },
      {
        category: HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold: HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
      },
      {
        category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold: HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
      },
      {
        category: HarmCategory.HARM_CATEGORY_UNSPECIFIED,
        threshold: HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
      },
    ],
  } as GenerativeConfig;
};

export class SafetySettings {
  static categoryLabel = (category: HarmCategory): string => {
    switch (category) {
      case HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:
        return 'Dangerous Content';
      case HarmCategory.HARM_CATEGORY_HATE_SPEECH:
        return 'Hate Speech';
      case HarmCategory.HARM_CATEGORY_HARASSMENT:
        return 'Harassment';
      case HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:
        return 'Sexually Explicit';
      default:
        return 'Undefined';
    }
  };

  static thresholdLabel = (threshold: number): string => {
    switch (threshold) {
      case 0:
        return `Unspecified`;
      case 1:
        return `Low and Above`;
      case 2:
        return `Medium and Above`;
      case 3:
        return `Block High Only`;
      case 4:
        return `Block None`;
      default:
        return `Default`;
    }
  };

  static thresholdToNumber = (threshold: HarmBlockThreshold): number => {
    switch (threshold) {
      case HarmBlockThreshold.BLOCK_LOW_AND_ABOVE:
        return 1;
      case HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE:
        return 2;
      case HarmBlockThreshold.BLOCK_ONLY_HIGH:
        return 3;
      case HarmBlockThreshold.BLOCK_NONE:
        return 4;
      default:
        return 0;
    }
  };

  static numberToThreshold = (value: number | number[]): HarmBlockThreshold => {
    const input = Array.isArray(value) ? value[0] : value;
    switch (input) {
      case 0:
        return HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED;
      case 1:
        return HarmBlockThreshold.BLOCK_LOW_AND_ABOVE;
      case 2:
        return HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE;
      case 3:
        return HarmBlockThreshold.BLOCK_ONLY_HIGH;
      case 4:
        return HarmBlockThreshold.BLOCK_NONE;
      default:
        return HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED;
    }
  };
}