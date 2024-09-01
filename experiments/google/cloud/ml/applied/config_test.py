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

import unittest

from config import Config


class UtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config()

    def test_config_values(self):
        pid = self.config.value("project", "id")
        self.assertEquals(pid, "solutions-2023-mar-107")

    def test_int(self):
        depth = self.config.value("category", "depth")
        self.assertEquals(depth, 4)

    def test_list(self):
        filter = self.config.value("category", "filter")
        self.assertEquals(len(filter), 4)

    def test_bool(self):
        allow_nulls = self.config.value(key="allow_trailing_nulls")
        self.assertFalse(allow_nulls)
