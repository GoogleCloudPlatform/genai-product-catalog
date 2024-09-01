#  Copyright 2023 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Vertex Vector Search Integration Test.

Ensures we can access the vector store and nearest neighbors are returned 
the expected format. This integration test assumes:
-A Vector Store is already running and the appropriate variables have been set 
in config.py
-The test is run from an environment that has permission to call the API

https://cloud.google.com/vertex-ai/docs/vector-search/overview
"""
import logging
import unittest
import nearest_neighbors
from google.cloud.ml.applied.config import Config

logging.basicConfig(level=logging.INFO)

test_category = Config.value("test", "category")
num_neighbors = 3
emb1 = [0] * 1408
emb2 = [0] * 1408
embeds = [emb1, emb2]


class NearestNeighborsTest(unittest.TestCase):
    def test_nn_no_filter(self):
        res = nearest_neighbors.get_nn(embeds=embeds, num_neighbors=num_neighbors)
        logging.info(res)
        self.assertEqual(len(res), len(embeds) * num_neighbors)
        self.assertEqual(res[0]._fields, ("id", "distance"))

    def test_nn_with_filter(self):
        res = nearest_neighbors.get_nn(
            embeds=embeds, filters=[test_category], num_neighbors=num_neighbors
        )
        logging.info(res)
        self.assertEqual(len(res), len(embeds) * num_neighbors)
        self.assertEqual(res[0]._fields, ("id", "distance"))


if __name__ == "__main__":
    unittest.main()
