<<<<<<<< HEAD:demos/digital-commerce-adk/catalog_enrichment_agent/__init__.py
# Copyright 2024 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
========
# Copyright 2024 Google, LLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
# 
>>>>>>>> origin/main:demos/digital-commerce/example-dispatch.yaml
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
<<<<<<<< HEAD:demos/digital-commerce-adk/catalog_enrichment_agent/__init__.py
from . import agent
========

dispatch:

- url: "*/api/*"
  service: api

- url: "*/socket.io/*"
  service: api

- url: "<YOUR APP SPOT API URL>/*"
  service: api

- url: "*/favicon.ico"
  service: default

- url: "<YOUR APP SPOT DEFAULT URL>/*"
  service: default

>>>>>>>> origin/main:demos/digital-commerce/example-dispatch.yaml
