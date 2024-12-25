#   Copyright 2022 Google LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
from itertools import product

import common.model as model

example_image = model.Image(
    url='https://www.google.com/logos/doodles/2024/seasonal-holidays-2024-6753651837110333.2-la202124.gif',
    mime_type='image/gif', alt='Example Logo')

example_product = model.Product(
    name='Kobalt 46.1-in L x 37.2-in H 9-Drawers Rolling Black Wood Work Bench',
    sku='05044810',
    category='Tools > Tool Storage & Work Benches > Work Benches & Tops',
    short_description="""The Kobalt 46-In 9-Drawer Mobile Workstation is great for storing and organizing all your tools and hardware. The unit is made from high grade all welded steel construction with a tough, rust-resistant powder coat finish. 9 Drawers are soft-close full-extension and glide effortlessly on ball-bearing slides that can support up to 100 lbs. solid wood top with protective coating provides great work surface. You can charge your electronics and power tools even when the chest is locked via the integrated power strip with 4-outlets and 2-USB ports. An ergonomic handle and 5 in. x 2 in. casters allow you to easily move your cabinet around your workspace. Total weight capacity of the unit is 1,200lbs.""",
    long_description="""
* 100lbs soft-close full extension drawers for smooth opening and closing
* 9 Different sized drawers for storing and organizing all your tools and hardware
* All welded steel construction with a tough, rust-resistant powder coat finish
* Solid wood top with protective coating provides a 46-in x 18-in work surface
* Integrated power strip with 4-outlets and 2-USB ports for easy charging
* 4 5-In heavy-duty casters ( 2-fixed, 2-swivel with toe locks) can support up to 1,200lbs
* Pre-cut drawer liners for better protect chest from scratching
* Black steel tubular side handle for easily moving the workbench around workspace
* Built-in keyed lock keep your tools and hardware safe
    """,
    features=[model.ProductFeature(title='Innovative Workbench',
                                   body='100lbs soft-close full extension drawers for smooth opening and closing',
                                   images=[model.Image(
                                       url='https://salsify-ecdn.com/images/afa03f7c2ff7e465313e38287e12dc8c.avif',
                                       mime_type='image/avif', alt='Tool Chest - Front')])],
    specifications=[
        model.ProductSpecification(
            category='General',
            key='Color/Finish Family',
            value='Black'
        )
    ],
    images=[example_image]
)

example_review = model.Review(
    verified=True,
    sentiment_score = 95.0,
    title = 'Love at first use.',
    rating = 5,
    body = 'I love nearly all of the features about this tool chest, I only wish it had come with better wheels',
    product = example_product)

example_reviews = model.Reviews(
    aggregate_score = 95.0,
    product = example_product)