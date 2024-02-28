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

"""Functions related to product categorization."""
import logging
import re
from collections import defaultdict
from typing import Optional

from google.cloud.ml.applied.model import domain_model as m
from google.cloud.ml.applied.embeddings import embeddings
from google.cloud.ml.applied.knn import nearest_neighbors
from google.cloud.ml.applied.utils import utils
from google.cloud.ml.applied.config import Config

bq_client = utils.get_bq_client()
llm = utils.get_llm()

category_depth = Config.value(Config.SECTION_CATEGORY, "depth")
allow_trailing_nulls = Config.value(key="allow_trailing_spaces")
number_of_neighbors = Config.value(Config.SECTION_VECTORS, "number_of_neighbors")

bq = Config.SECTION_BIG_QUERY
table_product = Config.value(bq, "product_table")
column_id = Config.value(bq, "product_id_column")
column_categories = Config.value(bq, "product_category_column_list")


def join_categories(ids: list[str]) -> dict[str : list[str]]:
    """Given list of product IDs, join category names.

    Args:
        ids: list of product IDs used to join against master product table

    Returns:
        dict mapping product IDs to category name. The category name will be
        a list of strings e.g. ['level 1 category', 'level 2 category']
    """
    query = f"""
    SELECT
        {column_id},
        {','.join(column_categories[:category_depth])}
    FROM
        `{table_product}`
    WHERE
        {column_id} IN {str(ids).replace('[', '(').replace(']', ')')}
    """
    query_job = bq_client.query(query)
    rows = query_job.result()
    categories = defaultdict(list)
    for row in rows:
        for col in column_categories:
            if row[col]:
                categories[row[column_id]].append(row[col])
            else:
                if allow_trailing_nulls:
                    if col == column_categories[0]:
                        raise ValueError(
                            f"Top level category {col} for product {row[column_id]} is null"
                        )
                    else:
                        break  # return existing categories
                else:
                    raise ValueError(
                        f"Column {col} for product {row[column_id]} is null. To allow nulls update app.toml"
                    )
    return categories


def retrieve(
    desc: str,
    image: Optional[str] = None,
    base64: bool = False,
    filters: list[str] = [],
) -> list[dict]:
    """Returns list of categories based on nearest neighbors.

    This is a 'greedy' retrieval approach that embeds the provided desc and
    (optionally) image and returns the categories corresponding to the closest
    products in embedding space.

    Args:
        desc: user provided description of product
        image: can be local file path, GCS URI or base64 encoded image
        base64: True indicates image is base64. False (default) will be
          interpreted as image path (either local or GCS)
        filters: category prefix to restrict results to

    Returns:
        List of candidates sorted by embedding distance. Each candidate is a
        dict with the following keys:
            id: product ID
            category: category in list form e.g. ['level 1 category', 'level 2 category']
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
    categories = join_categories(ids)
    candidates = [
        {"category": categories[n.id[:-2]], "id": n.id, "distance": n.distance}
        for n in neighbors
    ]
    return sorted(candidates, key=lambda d: d["distance"])


def _rank(desc: str, candidates: list[list[str]]) -> list[list[str]]:
    """See rank() for docstring."""
    logging.info(f"Candidates:\n{candidates}")
    if not candidates:
        return []

    query = f"""
  Given the following product description:
  {desc}

  Rank the following categories from most relevant to least:
  {(chr(10) + '  ').join(['->'.join(cat) for cat in candidates])}

  Do not include any commentary in the result.
  """
    # chr(10) == \n. workaround since backslash not allowed in f-string in python < 3.12

    llm_parameters = {
        "max_output_tokens": 256,
        "temperature": 0.0,
    }
    response = llm.predict(query, **llm_parameters)
    res = response.text.splitlines()
    if not res:
        raise ValueError(
            "ERROR: No LLM response returned. This seems to be an intermittent bug"
        )

    logging.info(f"Response:\n{res}")
    formatted_res = [
        re.sub(r"^\s*(\d+\.|\*|-)\s+", "", line.strip()).split("->") for line in res
    ]
    formatted_res = [
        res for res in formatted_res if len(res) == len(candidates[0])
    ]  # remove answers that don't match expected length

    unique_res = list(dict.fromkeys([tuple(item) for item in formatted_res]))
    logging.info(f"Formatted Response:\n {unique_res}")
    if not unique_res:
        raise ValueError("ERROR: No responses returned in expected format")
    return unique_res


def rank(desc: str, candidates: list[list[str]]) -> list[list[str]]:
    """Use an LLM to rank candidates by description.

    Args:
      desc: user provided description of product
      candidates: list of categories. Each category is in list form
        e.g. ['level 1 category', 'level 2 category'] so it's a list of lists

    Returns:
      The candidates ranked by the LLM from most to least relevant. If there are
      duplicate candidates the list is deduped prior to returning
    """
    try:
        return _rank(desc, candidates)
    except ValueError as e:
        logging.error(e)
        logging.error("Falling back to original candidate ranking.")
        return list(dict.fromkeys([tuple(list_item) for list_item in candidates]))


def retrieve_and_rank(
    desc: str,
    image: Optional[str] = None,
    base64: bool = False,
    filters: list[str] = [],
) -> m.CategoryList:
    """Wrapper function to sequence retrieve and rank functions.

    Args:
        desc: user provided description of product
        image: can be local file path, GCS URI or base64 encoded image
        base64: True indicates image is base64. False (default) will be
          interpreted as image path (either local or GCS)
        num_neigbhors: number of nearest neighbors to return for EACH embedding
        filters: category prefix to restrict results to

    Returns:
      The candidates ranked by the LLM from most to least relevant. If there are
      duplicate candidates the list is deduped prior to returning
    """
    candidates = retrieve(desc, image, base64, filters)
    if filters and not candidates:
        return [["ERROR: No existing products match that category"]]

    return m.CategoryList(
        values=rank(desc, [candidate["category"] for candidate in candidates])
    )
