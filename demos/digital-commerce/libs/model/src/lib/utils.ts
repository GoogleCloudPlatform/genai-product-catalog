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

import { Image } from './model';

export const formatIndexedPlaceholders = (
  template: string,
  ...args: string[]
) => {
  return template.replace(/{([0-9]+)}/g, function (match, index) {
    return typeof args[index] === 'undefined' ? match : args[index];
  });
};

export const stripBase64Prefix = (
  input: string | ArrayBuffer | null
): string => {
  if (input) {
    if (input instanceof ArrayBuffer) {
      const decoder = new TextDecoder();
      const temp = decoder.decode(input);
      return temp.substring(temp.indexOf(',') + 1);
    } else {
      return input.substring(input.indexOf(',') + 1);
    }
  }
  return '';
};

export const imageToBase64 = (
  url: string,
  callback: (image: Image) => void
): void => {
  fetch(url)
    .then((response) => response.blob())
    .then((blob) => {
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = () => {
        const base64String = reader.result;
        const mimeType = blob.type;
        callback({ uri: url, base64: base64String, type: mimeType } as Image);
      };
    });
};



