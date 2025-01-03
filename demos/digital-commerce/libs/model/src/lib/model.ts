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
import { GenerativeConfig } from './gemini';

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


