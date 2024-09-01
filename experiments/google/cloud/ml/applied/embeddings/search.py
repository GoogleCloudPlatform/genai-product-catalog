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


from google.cloud import aiplatform_v1

from google.cloud.ml.applied.embeddings import embeddings
from google.cloud.ml.applied.utils import utils
from google.cloud.ml.applied.config import Config

index_client = utils.get_vector_search_index_client()

search_index_id = Config.value(Config.SECTION_VECTORS, "index_path")


def insert_dp(dp_id: str, emb: list[float], cat=[]):
    print(
        "Inserting data point id "
        + dp_id
        + " into vector search index "
        + str(search_index_id)
    )
    try:
        if cat:
            insert_datapoints_payload = aiplatform_v1.IndexDatapoint(
                datapoint_id=dp_id,
                feature_vector=emb,
                restricts=[{"namespace": "L0", "allow_list": cat}],
            )
        else:
            insert_datapoints_payload = aiplatform_v1.IndexDatapoint(
                datapoint_id=dp_id, feature_vector=emb
            )
        upsert_request = aiplatform_v1.UpsertDatapointsRequest(
            index=search_index_id, datapoints=[insert_datapoints_payload]
        )

        res = index_client.upsert_datapoints(request=upsert_request)
        print(
            res
        )  # If successful, the response body is empty [https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.indexes/upsertDatapoints].

    except Exception as e:
        print("An error occurred:", e)
        print("Unable to insert into vector search index")


def upsert_dp(prod_id: str, desc: str, image: str, cat=[]):
    res = embeddings.embed(desc, image, base64=False)

    if desc:
        dp_id = prod_id + "_T"
        emb = list(res.text_embedding)
        insert_dp(dp_id, emb, cat)
    if image:
        dp_id = prod_id + "_I"
        emb = list(res.image_embedding)
        insert_dp(dp_id, emb, cat)


def remove_dp(dp_id: str):
    print(
        "Deleting data point id "
        + dp_id
        + " from vector search index"
        + str(search_index_id)
    )
    try:
        remove_request = aiplatform_v1.RemoveDatapointsRequest(
            index=search_index_id, datapoint_ids=[dp_id]
        )

        res = index_client.remove_datapoints(request=remove_request)
        print(
            res
        )  # If successful, the response body is empty[https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.indexes/removeDatapoints}
    except Exception as e:
        print("An error occurred:", e)
        print("Unable to delete/remove data point from vector search index")


def delete_dp(prod_id: str):
    try:
        remove_dp(prod_id + "_T")
    except Exception as e:
        print("Product description does not exist", e)

    try:
        remove_dp(prod_id + "_I")
    except Exception as e:
        print("Product image does not exist", e)
