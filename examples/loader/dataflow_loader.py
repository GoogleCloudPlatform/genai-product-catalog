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

import argparse
import json
import logging
from typing import Optional

import apache_beam as beam
import jsonpickle
import pandas as pd
import requests
import vertexai
from apache_beam.options.pipeline_options import PipelineOptions
from models.model import FILE_COLUMNS, parse_row
from vertexai.vision_models import (
    Image,
    MultiModalEmbeddingModel,
    MultiModalEmbeddingResponse,
)

import google.cloud.logging
from google.cloud import bigquery, storage


def get_multimodal_embeddings(
    image_path: str,
    contextual_text: Optional[str] = None,
    project_id: str = "customermod-genai-sa",
    location: str = "us-central1",
    dimension: int = 1408,
) -> MultiModalEmbeddingResponse:
    vertexai.init(project=project_id, location=location)

    embedding_model = MultiModalEmbeddingModel.from_pretrained(
        "multimodalembedding@001"
    )

    image = Image.load_from_file(image_path)

    embeddings = embedding_model.get_embeddings(
        image=image,
        contextual_text=contextual_text,
        dimension=dimension,
    )
    print(f"Image Embedding: {embeddings.image_embedding[0:10]}")
    print(f"Text Embedding: {embeddings.text_embedding[0:10]}")

    return embeddings


def product_to_json(product):
    # Serialize a Product object to a JSON string using jsonpickle.
    # Setting unpicklable=False generates a JSON representation of the object
    # that can be easily converted back to a dictionary, but not necessarily back to the original object.

    json_str = jsonpickle.encode(product, unpicklable=False)
    log(f"[product_to_json]{json_str}")
    return json_str


class ParseRow(beam.DoFn):
    def process(self, element):
        try:
            # Assuming 'element' is a dictionary representation of the CSV row
            product = parse_row(pd.Series(element), True)
            if product:
                # Yielding as a tuple (success indicator, data)
                print(product.headers[0].name)
                yield "success", product
        except Exception as e:
            # Yielding as a tuple (failure indicator, error message)
            yield "failure", str(e)


def log(text: str):
    try:
        client = google.cloud.logging.Client()
        logger = client.logger("RDM_Dataflow")
        logger.log_text(text)
        print(text)
    except Exception as e:
        logging.info(f"[RDM_Dataflow]{e}")
        print(f"[RDM_Dataflow]Exception:{e}")
        raise e


class DownloadImage(beam.DoFn):
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name

    def process(self, element):
        # Create the storage client within the process method
        client = storage.Client()
        try:
            product = element  # Assuming element is the product object
            print(f"Processing product: {element.headers[0].name}")
            image_url = product.headers[0].images[0].origin_url
            response = requests.get(image_url)
            if response.status_code == 200:
                blob_name = f"images/{product.business_keys[1].value}.jpg"
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(blob_name)
                blob.upload_from_string(response.content, content_type="image/jpeg")
                print("upload done")
                gcs_url = f"gs://{self.bucket_name}/{blob_name}"
                product.headers[0].images[0].url = gcs_url
                print(gcs_url)
                yield "success", product
            else:
                print(f"[Error]{image_url}")
                yield "failure", f"Failed to download image from {image_url}"
        except Exception as e:
            yield "failure", str(e)


class CallEmbeddingAPI(beam.DoFn):
    def __init__(self, project_id, location):
        self.project_id = project_id
        self.location = location

    def process(self, element):
        log(f"Embedding product: {element.headers[0].name}")
        try:
            product = element  # Assuming element is a tuple (status, product)
            image_path = product.headers[0].images[0].url
            contextual_text = (
                product.headers[0].name
                + product.headers[0].long_description
                + product.headers[0].brand
            )
            embeddings = get_multimodal_embeddings(
                project_id=self.project_id,
                location=self.location,
                image_path=image_path,
                contextual_text=contextual_text,
            )
            # Assuming you want to store or do something with the embeddings here
            # For simplicity, just printing the embeddings
            product.image_embedding = embeddings.image_embedding
            product.text_embedding = embeddings.text_embedding
            log("embedding finished")
            yield "success", product
        except Exception as e:
            log(f"[CallEmbeddingAPI][Error]{e}")
            yield "failure", str(e)


def partition_fn(element, num_partitions):
    log(f"...partition_fn...{num_partitions}:{element}")
    return 0 if element[0] == "success" else 1


class AggregateToList(beam.CombineFn):
    def create_accumulator(self):
        return []

    def add_input(self, accumulator, input):
        json_input = json.loads(input)
        accumulator.append(json_input)
        # accumulator.append(input)
        return accumulator

    def merge_accumulators(self, accumulators):
        return [item for sublist in accumulators for item in sublist]

    def extract_output(self, accumulator):
        return accumulator


class WriteJsonToBigQuery(beam.DoFn):
    def __init__(self, project_id: str, bq_table_id: str):
        self.project_id = project_id
        self.fully_qualified_table = bq_table_id

    def process(self, element):
        try:
            json_data = json.loads(element)
            log(f"[WriteJsonToBigQuery]element:{element[0:100]}")
            status, data = json_data
            log(f"* status={status}")
            if status == "success":
                log(f"[WriteJsonToBigQuery]data:{json.dumps(data)[0:100]}")
                bq_client = bigquery.Client(self.project_id)
                table = bq_client.get_table(self.fully_qualified_table)
                result = bq_client.insert_rows_json(table, [data])
                log(
                    f"[WriteJsonToBigQuery]Insert [{self.fully_qualified_table}] Completed:{result}"
                )

                if result is not None and result != "":
                    log(
                        f"""
===> Error Json <===
{data}
===> End Error Json <===
                        """
                    )
            return element
        except Exception as e:
            log(f"[WriteJsonToBigQuery][Exception] [{e}")
            raise e


class WriteToGCS(beam.DoFn):
    def __init__(self, project_id, bucket, file_name):
        self.project_id = project_id
        self.bucket = bucket
        self.file_name = file_name

    def process(self, element):
        print(f"[WriteToGCS]:{self.bucket} | {self.file_name}")
        client = storage.Client(self.project_id)
        bucket = client.get_bucket(self.bucket)
        blob = bucket.blob(self.file_name)
        blob.upload_from_string(f"{element}")


class ConvertStringToDict(beam.DoFn):
    def process(self, element):
        dict_data = json.loads(element)
        yield dict_data


def run(argv=None, save_main_session=True):
    """Main entry point; defines and runs the wordcount pipeline."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input_subscription",
        dest="subscription",
        help="Input PubSub subscription of the form "
        '"projects/<PROJECT>/subscriptions/<SUBSCRIPTION>."',
    )
    parser.add_argument(
        "--bucket",
        dest="bucket",
        required=True,
        help="GCS Bucket name for storing product images and information.",
    )
    parser.add_argument(
        "--bq-table-id",
        dest="bq_table_id",
        required=True,
        help="Full qualified BigQuery dataset id in <DATASET_ID>.<TABLE_ID> format.",
    )

    known_args, pipeline_args = parser.parse_known_args(argv)

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    pipeline_options = PipelineOptions(
        pipeline_args,
        save_main_session=True,
        streaming=True,
        setup_file="/template/setup.py",
    )

    project_id = ""

    if "--project" in pipeline_args:
        project_id = pipeline_args[pipeline_args.index("--project") + 1]
    elif "-p" in pipeline_args:
        project_id = pipeline_args[pipeline_args.index("-p") + 1]
    else:
        items = [item for item in pipeline_args if item.startswith("--project=")]
        if len(items) > 0:
            project_id = items[0].split("=")[1]

    subscription_id = known_args.subscription
    bucket_name = known_args.bucket
    bq_table_id = f"{project_id}.{known_args.bq_table_id}"

    print(f"*** project_id={project_id}")
    with beam.Pipeline(options=pipeline_options) as p:
        print(f"** Starting pipeline...{subscription_id}")
        print(f"""FILE_COLUMNS={FILE_COLUMNS}""")

        raw_data = (
            p
            | "Read Pub/Sub"
            >> beam.io.gcp.pubsub.ReadStringsFromPubSub(subscription=subscription_id)
            | "Convert Message to Row" >> beam.ParDo(ConvertStringToDict())
        )

        raw_data | "print row" >> beam.Map(print)

        # skipping RDM transform and
        parsed_data = (
            raw_data
            | "Parse Row" >> beam.ParDo(ParseRow())
            | "Partition by Parse Success" >> beam.Partition(partition_fn, 2)
        )

        success_data, failed_parse = parsed_data

        print(f"bucket_name...${bucket_name}")
        # Process successfully parsed data further
        processed_data = (
            success_data
            | "Extract Success Data"
            >> beam.Map(lambda x: x[1])  # Extract the product object from the tuple
            | "Download Image to GCS"
            >> beam.ParDo(DownloadImage(bucket_name=bucket_name))
            | "Partition by Download Success" >> beam.Partition(partition_fn, 2)
        )

        success_downloads, failed_downloads = processed_data

        # # Call Embedding API on successfully downloaded images
        embedding_results = (  # noqa: F841
            success_downloads
            | "Extract Success Downloads"
            >> beam.Map(lambda x: x[1])  # Extract the product object from the tuple
            | "Call Embedding API"
            >> beam.ParDo(
                CallEmbeddingAPI(project_id=project_id, location="us-central1")
            )
            | "Convert to JSON" >> beam.Map(product_to_json)
            | "Write to BigQuery"
            >> beam.ParDo(
                WriteJsonToBigQuery(project_id=project_id, bq_table_id=bq_table_id)
            )
        )


if __name__ == "__main__":
    run()
