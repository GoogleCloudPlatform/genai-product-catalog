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


"""Test Rest API.

Make sure to update the ENDPOINT variable as appropriate before running.
"""
import logging
import requests
import unittest
import config
from google.auth.transport.requests import Request
from google.oauth2 import id_token

logging.basicConfig(level=logging.INFO)

# ENDPOINT = 'http://localhost:8080/genai/v1/' # UPDATE AS NEEDED
# ENDPOINT = 'http://127.0.0.1:8000/genai/v1/' # UPDATE AS NEEDED
# ENDPOINT = 'https://catalog-full-functionality-olzeixpw4q-uc.a.run.app/genai/v1/' # UPDATE AS NEEDED
ENDPOINT = "https://ml2-dot-retail-shared-demos.uc.r.appspot.com/genai/v1/"
open_id_connect_token = id_token.fetch_id_token(Request(), "client_id")
headers = {"Authorization": f"Bearer {open_id_connect_token}"}

# test_desc = 'Timewel 1100-N1949_S Analog Watch - For Women - Buy Timewel 1100-N1949_S Analog Watch - For Women 1100-N1949_S Online at Rs.855 in India Only at Flipkart.com. - Great Discounts, Only Genuine Products, 30 Day Replacement Guarantee, Free Shipping. Cash On Delivery!'
# image_uri = "gs://prod_cat_demo/flipkart_20k_oct26/dbdac18a8ee5a8a48238b9685c96e90a_0.jpg"
# image_url = "http://img5a.flixcart.com/image/short/u/4/a/altht-3p-21-alisha-38-original-imaeh2d5vm5zbtgg.jpeg"
# product_id = 'dbdac18a8ee5a8a48238b9685c96e90a'
# cat = ['Watches']  #Top level filter L0

test_desc = config.TEST_DESCRIPTION
image_uri = config.TEST_GCS_IMAGE
image_url = config.TEST_IMAGE_URL
product_id = config.TEST_PRODUCT_ID
cat = [config.TEST_CATEGORY_L0]


class APITest(unittest.TestCase):
    def test_category(self):
        res = requests.post(
            ENDPOINT + "categories/",
            json={"description": test_desc, "image": image_uri},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)
        self.assertIsInstance(res.json()[0], list)
        self.assertIsInstance(res.json()[0][0], str)
        logging.info(res.json())

    def test_category_text_only(self):
        res = requests.post(
            ENDPOINT + "categories/", json={"description": test_desc}, headers=headers
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)
        self.assertIsInstance(res.json()[0], list)
        self.assertIsInstance(res.json()[0][0], str)
        logging.info(res.json())

    def test_category_with_filter(self):
        res = requests.post(
            ENDPOINT + "categories/",
            json={"description": test_desc, "category": [config.TEST_CATEGORY_L0]},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)
        self.assertIsInstance(res.json()[0], list)
        self.assertIsInstance(res.json()[0][0], str)
        logging.info(res.json())

    def test_attributes(self):
        res = requests.post(
            ENDPOINT + "attributes/",
            json={"description": test_desc, "image": image_uri},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), dict)
        self.assertGreater(len(res.json()), 0)
        logging.info(res.json())

    def test_attributes_with_filter(self):
        res = requests.post(
            ENDPOINT + "attributes/",
            json={
                "description": test_desc,
                "image": image_uri,
                "category": [config.TEST_CATEGORY_L0],
            },
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), dict)
        self.assertGreater(len(res.json()), 0)
        logging.info(res.json())

    def test_attributes_from_image_url(self):
        res = requests.post(
            ENDPOINT + "image_to_attributes/",
            params={"image": image_url},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), dict)
        self.assertGreater(len(res.json()), 0)
        logging.info(res.json())

    def test_attributes_from_image_uri(self):
        res = requests.post(
            ENDPOINT + "image_to_attributes/",
            params={"image": image_uri},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), dict)
        self.assertGreater(len(res.json()), 0)
        logging.info(res.json())

    def test_desc_from_image_url(self):
        res = requests.post(
            ENDPOINT + "image_to_description/",
            params={"image": image_url},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.text, str)
        logging.info(res.text)

    def test_desc_from_image_uri(self):
        res = requests.post(
            ENDPOINT + "image_to_description/",
            params={"image": image_uri},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.text, str)
        logging.info(res.text)

    def test_update_vector_search_index(self):
        res = requests.post(
            ENDPOINT + "update_vector_search_index/",
            params={"product_id": product_id},
            json={
                "description": test_desc,
                "image": image_uri,
                "category": [config.TEST_CATEGORY_L0],
            },
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.text, str)
        logging.info(res.text)

    def test_generate_marketing_copy(self):
        att = "{'Case / Bezel Material': 'Steel Case', 'Dial Color': 'Black', 'Dial Shape': 'Round', 'Ideal For': 'Women', 'Mechanism': 'Quartz', 'Occasion': 'Casual, Formal, Party-Wedding', 'Power Source': 'Battery Powered', 'Scratch Resistant': 'Yes', 'Strap Color': 'Black', 'Strap Material': 'Genuine Leather Strap', 'Strap Type': 'Leather', 'Style Code': '1100-N1949_S', 'Type': 'Analog'}"
        res = requests.post(
            ENDPOINT + "marketing/",
            params={"description": test_desc},
            json={"attributes": att},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.text, str)
        logging.info(res.text)

    def test_remove_product_from_vector_search(self):
        res = requests.post(
            ENDPOINT + "remove_product_from_vector_search/",
            params={"product_id": product_id},
            json={"description": test_desc, "image": image_uri},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.text, str)
        logging.info(res.text)


if __name__ == "__main__":
    unittest.main()
