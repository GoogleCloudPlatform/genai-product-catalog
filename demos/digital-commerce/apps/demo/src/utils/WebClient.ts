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

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL_BASE;

// Authentication is handled via IAP / session cookies (`withCredentials: true`)
// or an ephemeral in-memory bearer token passed at runtime via `setApiAuthToken`.
// Static API secrets must never be inlined into the public Vite bundle via `VITE_*`.
let runtimeBearerToken: string | null = null;

export function setApiAuthToken(token: string | null): void {
  runtimeBearerToken = token?.trim() || null;
  if (runtimeBearerToken) {
    AxiosInstance.defaults.headers.common['Authorization'] =
      `Bearer ${runtimeBearerToken}`;
  } else {
    delete AxiosInstance.defaults.headers.common['Authorization'];
  }
}

export function getApiAuthToken(): string | null {
  return runtimeBearerToken;
}

const AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  withCredentials: true,
});
AxiosInstance.defaults.headers.common['Content-Type'] = 'application/json';

export default AxiosInstance;
