# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os

from pydoc_markdown.interfaces import Context
from pydoc_markdown.contrib.loaders.python import PythonLoader
from pydoc_markdown.contrib.renderers.markdown import MarkdownRenderer

title = sys.argv[1]

context = Context(directory=os.getcwd())
loader = PythonLoader(search_path=["google/cloud/ml/applied"])
renderer = MarkdownRenderer(render_module_header=False)

loader.init(context)
renderer.init(context)

modules = loader.load()

print(
    """
---
title: "{0}"
weight: 4
---

""".format(title)
)

print(renderer.render_to_string(modules))
