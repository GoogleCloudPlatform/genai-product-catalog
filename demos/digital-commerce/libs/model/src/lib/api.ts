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

import { BatchProduct, Config, Image } from './model';

export interface ErrorResponse {
  code?: number;
  error: string;
}

export interface ConfigurationRequest {
  sessionID: string;
  config: Config;
}

export interface ConfigurationResponse {
  sessionID: string;
  message: string;
}

export interface TextPromptRequest {
  sessionID: string;
  prompt: string;
}

export interface SessionPromptPayloadRequest<T> {
  sessionID: string;
  prompt: string;
  value: T;
}

export interface ImagePromptRequest extends SessionPromptPayloadRequest<Image[]> {}

export interface AudioPromptRequest extends SessionPromptPayloadRequest<string> {
  type: string;
  size: number;
}

export interface AudioResponse {
  transcript: string;
  value: unknown;
}

export interface VideoPromptRequest extends SessionPromptPayloadRequest<string> {
  type: string;
  categoryPrompt: string
  productDetailPrompt: string
}

export interface BatchPromptRequest {
  sessionID: string
  values: BatchProduct[]
};
