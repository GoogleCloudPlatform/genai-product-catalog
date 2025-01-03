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
import { GridRowsProp } from '@mui/x-data-grid';
import {BatchProduct, Config, languages, gemini, Product} from 'model';
import {Socket} from 'socket.io-client';

export const CONFIG_KEY = '__RET_CFG_KeY__';

export interface BatchProductGridItem extends BatchProduct, GridRowsProp {

}

export interface BatchState {
    socket: Socket;
    setProducts: (products: Product[]) => void;
    products: Product[];
}

export interface SessionIDState {
    sessionID: string;
    setSessionID: (value: string) => void;
}

export interface ConfigState {
    config: Config;
    setConfig: (config: Config) => void;
}

export interface ProductState {
    product: Product;
    setProduct: (product: Product) => void;
}

export interface Interlocutor {
    role: string;
    value: string;
}

export interface ConversationState {
    conversation: Interlocutor[]
    setConversation: (value: Interlocutor[]) => void
    socket: Socket
}

export const defaultConfig = (): Config => {
    const existingConfigString = sessionStorage.getItem(CONFIG_KEY);
    let existingConfig: Config | null = null;

    if (existingConfigString) {
        existingConfig = JSON.parse(existingConfigString) as Config;
    }

    if (existingConfig) {
        return existingConfig;
    }

    const conf = {} as Config;
    conf.defaultLanguage = languages.DEFAULT_LANGUAGE;
    conf.customerName = '';
    conf.engineerLdap = '';

    conf.generativeConfig = gemini.NewGenerativeConfig(
        'You are an retail merchandising expert capable of describing, categorizing, and answering questions about products for a retail catalog and will ground answers using google when possible.'
    );

    // The more categories, the longer it will take to generate
    conf.promptDetectCategories = `
    Execute the following instructions:
    - Suggest the top 2 categories and their top 25 attributes from the image.
    - The category hierarchy must be 4 levels deep, separated by ' > ' character.
        
    Example JSON Output: [\${category_model}]`.trim();

    conf.promptExtractProductDetail = `
    Execute the following instructions and ground that is provided:
    - Extract the product name as the attribute 'name'.
    - Write an enriched product description in markdown format for a retailers online catalog as the attribute 'description'.
    - Write the HTML SEO description and keywords for the product as 'seoHtmlHeader'
    - Extract the product specific values for the attributes from the following attributes: \${category_attributes} as a json array of attributeValues like: \${product_attribute_value_model}
    - If the product is edible, include nutritional as additional attributeValues.

    - Example JSON Output: \${product_json}`.trim();

    conf.promptTranslateProductDetail = `
    Execute the following instructions:
    - Translate the json values in this JSON Object: \${product_json} from language: \${base_language} to: \${target_language}
    - If there is a unit of measure or numeric value convert the value into the most common unit of measure for the target language for the type of product.
    - Be as specific as possible using natural dialect.`.trim();

    conf.promptVideo = `
    Execute the following instructions:
    - Ignore and people and their clothing and or brands on their clothing.
    - Extract all of the product attributes as key value pairs.`.trim();

    return conf;
};