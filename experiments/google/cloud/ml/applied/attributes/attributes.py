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
#

"""Functions related to attribute generation."""
import json
import logging
from typing import Optional

from google.cloud.ml.applied.model import domain_model as m
from google.cloud.ml.applied.embeddings import embeddings
from google.cloud.ml.applied.utils import utils
from google.cloud.ml.applied.knn import nearest_neighbors
from google.cloud.ml.applied.config import Config

bq_client = utils.get_bq_client()
llm = utils.get_llm()


def join_attributes_desc(ids: list[str]) -> dict[str:dict]:
    """
    Gets the attributes and description for given product IDs.

    Args:
        ids: The product IDs to get the attributes for.

    Returns
        dict mapping product IDs to attributes and descriptions. Each ID will
        map to a dict with the following keys:
            attributes: e.g. {'color':'green', 'pattern': striped}
            description: e.g. 'This is a description'
    """
    bq = Config.SECTION_BIG_QUERY
    table_name = Config.value(bq, "product_table")
    column_id = Config.value(bq, "product_id_column")
    column_attributes = Config.value(bq, "product_attributes_column")
    column_description = Config.value(bq, "product_description_column")

    query = f"""
    SELECT
        {column_id},
        {column_attributes},
        {column_description}
    FROM
        `{table_name}`
    WHERE
        {column_id} IN {str(ids).replace('[', '(').replace(']', ')')}
    """
    query_job = bq_client.query(query)
    rows = query_job.result()
    attributes = {}
    for row in rows:
        id_value = row[column_id]
        logging.info(row)
        if isinstance(row[column_attributes], str):
            attributes[id_value] = {
                "attributes": json.loads(row[column_attributes]),
                "description": row[column_description],
            }
        else:
            attributes[id_value] = {
                "attributes": {},
                "description": row[column_description],
            }

    return attributes


def retrieve(
    desc: str,
    category: Optional[str] = None,
    image: Optional[str] = None,
    base64: bool = False,
    filters: list[str] = [],
) -> list[dict]:
    """Returns list of attributes based on nearest neighbors.

    Embeds the provided desc and (optionally) image and returns the attributes
    corresponding to the closest products in embedding space.

    Args:
        desc: user provided description of product
        category: category of the product
        image: can be local file path, GCS URI or base64 encoded image
        base64: True indicates image is base64. False (default) will be
          interpreted as image path (either local or GCS)
        filters: category prefix to restrict results to

    Returns:
        List of candidates sorted by embedding distance. Each candidate is a
        dict with the following keys:
            id: product ID
            attributes: attributes in dict form e.g. {'color':'green', 'pattern': 'striped'}
            description: string describing product
            distance: embedding distance in range [0,1], 0 being the closest match
    """
    res = embeddings.embed(desc, image, base64)
    embeds = (
        [res.text_embedding, res.image_embedding]
        if res.image_embedding
        else [res.text_embedding]
    )
    neighbors = nearest_neighbors.get_nn(embeds, filters)
    if not neighbors:
        return []
    ids = [n.id[:-2] for n in neighbors]  # last 3 chars are not part of product ID
    attributes_desc = join_attributes_desc(ids)
    candidates = [
        {
            "attributes": attributes_desc[n.id[:-2]]["attributes"],
            "description": attributes_desc[n.id[:-2]]["description"],
            "id": n.id,
            "distance": n.distance,
        }
        for n in neighbors
    ]
    return sorted(candidates, key=lambda d: d["distance"])


def generate_prompt(desc: str, candidates: list[dict]) -> str:
    """Populate LLM prompt template.

    Args:
        desc: product description
        candidates: list of dicts with the following keys:
            attributes: attributes in dict form e.g. {'color':'green', 'pattern': 'striped'}
            description: string describing product

    Returns: prompt to feed to LLM
    """
    examples = ""
    for candidate in candidates:
        examples += "Description: " + candidate["description"] + "\n"
        examples += (
            "Attributes:\n"
            + "|".join([k + ":" + v for k, v in candidate["attributes"].items()])
            + "\n\n"
        )

    prompt = f"""
Here are examples of Product Descriptions followed by Attributes:

{examples}

INSTRUCTIONS:
Generate attributes based on the description below.
Each attribute should be a key:value pair.
Do not write any values that contain "NA" on the list. Examples "Material: NA" or "Type: NA"
Use a pipe separator "|" to separate attributes.

Description: {desc}
Attributes:
    """
    return prompt


def parse_answer(ans: str) -> dict[str, str]:
    """Translate LLM response into dict.

    Args:
        ans: '|' separated key value pairs e.g. 'color:red|size:large'
    Returns:
        ans as a dictionary
    """
    d = {}
    for a in ans.split("|"):
        k, v = a.split(":")
        d[k.strip()] = v.strip()
    return d


def generate_attributes(desc: str, candidates: list[dict]) -> m.AttributeValue:
    """Use an LLM to determine attributes given nearest neighbor candidates

    Args:
        desc: product description
        candidates: list of dicts with the following keys:
            attributes: attributes in dict form e.g.
            {'color':'green', 'pattern': 'striped'}
            description: string describing product

    Returns: attributes in dict form e.g. {'color':'green', 'pattern': 'striped'}
    """
    prompt = generate_prompt(desc, candidates)
    llm_parameters = {
        "max_output_tokens": 256,
        "temperature": 0.0,
    }
    response = llm.predict(prompt, **llm_parameters)
    res = response.text
    if not res:
        raise ValueError(
            "ERROR: No LLM response returned. This seems to be an intermittent bug"
        )
    try:
        formatted_res = parse_answer(res)
    except Exception as e:
        logging.error(e)
        raise ValueError(f"LLM Response: {res} is not in the expected format")
    return m.dict_to_attribute_values(formatted_res)


def retrieve_and_generate_attributes(
    desc: str,
    category: Optional[str] = None,
    image: Optional[str] = None,
    base64: bool = False,
    filters: list[str] = [],
) -> m.ProductAttributes:
    """RAG approach to generating product attributes.

    Since LLM answers are not always well formatted, if we fail to parse the
    LLM answer we fall back to a greedy retrieval approach.

    Args:
        desc: user provided description of product
        category: category of the product
        image: can be local file path, GCS URI or base64 encoded image
        base64: True indicates image is base64. False (default) will be
          interpreted as image path (either local or GCS)
        num_neigbhors: number of nearest neighbors to return for EACH embedding
        filters: category prefix to restrict results to

    Returns: attributes in dict form e.g.
    {'color':'green', 'pattern': 'striped'}
    """
    candidates = retrieve(desc, category, image, base64, filters)
    if filters and not candidates:
        return {"error": "ERROR: no existing products match that category"}
    try:
        return m.ProductAttributes(
            product_attributes=generate_attributes(desc, candidates)
        )
    except ValueError as e:
        logging.error(e)
        logging.error("Falling back to greedy approach")
        return m.ProductAttributes(product_attributes=candidates[0]["attributes"])
