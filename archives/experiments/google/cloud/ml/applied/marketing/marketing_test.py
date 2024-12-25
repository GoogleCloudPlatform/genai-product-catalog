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

import unittest
import logging

from google.cloud.ml.applied.marketing import marketing
from google.cloud.ml.applied.model.domain_model import (
    MarketingRequest,
    TextValue,
    AttributeValue,
)

logging.basicConfig(level=logging.INFO)


class MarketingTest(unittest.TestCase):
    def test_generate_marketing_copy(self):
        desc = "Men’s Hooded Puffer Jacket"
        attributes = [
            AttributeValue(attribute_name="color", attribute_value="green"),
            AttributeValue(attribute_name="pattern", attribute_value="striped"),
            AttributeValue(attribute_name="material", attribute_value="down"),
        ]

        req = MarketingRequest(description=desc, attributes=attributes)

        res = marketing.generate_marketing_copy(req)
        self.assertIsInstance(res, TextValue)
        logging.info(res)


if __name__ == "__main__":
    unittest.main()
