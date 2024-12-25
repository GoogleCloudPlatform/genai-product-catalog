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


"""Attribute Unit and Integration Tests.

These tests assume:
-The appropriate variables have been set in config.py
-The test is run from an environment that has permission to call cloud APIs
"""
import logging
import unittest
from google.cloud.ml.applied.attributes import attributes
from google.cloud.ml.applied.config import Config

logging.basicConfig(level=logging.INFO)


class AttributesTest(unittest.TestCase):
    def setUp(self):
        test = Config.SECTION_TEST
        vectors = Config.SECTION_VECTORS
        self.testProductId = Config.value(test, "product_id")

        self.numberOfNeighbors = int(Config.value(vectors, "number_of_neighbors"))

        self.testImage = Config.value(test, "gcs_image")

        self.testCategory = Config.value(test, "category")

    def test_join_attributes_desc(self):
        res = attributes.join_attributes_desc([self.testProductId])
        self.assertIsNotNone(res)
        self.assertIsInstance(res, dict)
        for k, v in res.items():
            self.assertIsInstance(k, str)
            self.assertIsInstance(v, dict)
            self.assertEqual(set(v.keys()), {"attributes", "description"})
        logging.info(res[self.testProductId]["attributes"])
        logging.info(res[self.testProductId]["description"])

    def test_generate_prompt(self):
        desc = "This is an orange"
        candidates = [
            {
                "description": "Apple",
                "attributes": {"Color": "green", "Taste": "sweet"},
            },
            {"description": "Banana", "attributes": {"Color": "yellow"}},
        ]
        res = attributes.generate_prompt(desc, candidates)
        logging.info(res)
        self.assertIsInstance(res, str)

    def test_retrieve_no_category(self):
        res = attributes.retrieve(
            desc="This is a test description", image=self.testImage
        )
        logging.info(res)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), self.numberOfNeighbors * 2)
        self.assertEqual(
            set(res[0].keys()), {"id", "attributes", "description", "distance"}
        )

    def test_generate_attributes_no_category(self):
        candidates = [
            {
                "description": "Apple",
                "attributes": {"Color": "green", "Taste": "sweet"},
            },
            {"description": "Banana", "attributes": {"Color": "yellow"}},
        ]
        res = attributes.generate_attributes("Orange", candidates)
        logging.info(res)
        self.assertGreater(len(res), 0)

    def test_parse_answer(self):
        res = attributes.parse_answer(" color: deep red |size:large")
        self.assertDictEqual(res, {"color": "deep red", "size": "large"})

    def test_retrieve_and_generate_attributes(self):
        res = attributes.retrieve_and_generate_attributes(
            desc="Fleece Jacket", image=self.testImage
        )
        logging.info(res)
        self.assertIsInstance(res, dict)
        self.assertGreater(len(res), 0)

    def test_retrieve_and_generate_attributes_with_filter(self):
        res = attributes.retrieve_and_generate_attributes(
            desc="Fleece Jacket",
            image=self.testImage,
            filters=[self.testCategory],
        )
        logging.info(res)
        self.assertIsInstance(res, dict)
        self.assertGreater(len(res), 0)

    def test_retrieve_and_generate_attributes_with_bad_filter(self):
        res = attributes.retrieve_and_generate_attributes(
            desc="Fleece Jacket",
            image=self.testImage,
            filters=["XYZunknowncategory"],
        )
        logging.info(res)
        self.assertIsInstance(res, dict)
        self.assertGreater(len(res), 0)


if __name__ == "__main__":
    unittest.main()
