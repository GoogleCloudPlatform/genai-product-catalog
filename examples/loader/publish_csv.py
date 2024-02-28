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

import argparse
from concurrent import futures
from google.cloud import pubsub_v1
from typing import Callable
import pandas as pd
from model import FILE_COLUMNS
import json


def read_csv(file_path: str) -> list[str]:
    # header = ""
    # lines = []

    # with open(file=file_path, mode="r") as f:
    #     all_lines = f.readlines()
    #     header = all_lines[0]
    #     lines = all_lines[1:]

    # # messages = [f"{header}{line}" for line in lines]
    # messages = list(set(lines))
    # print(len(messages))

    data = pd.read_csv(file_path, dtype=FILE_COLUMNS)
    data = data.drop_duplicates(subset=["product_name"])
    data = data.drop_duplicates(subset=["pid"])

    messages = data.to_dict("records")
    print(len(messages))
    return messages


def get_callback(
    publish_future: pubsub_v1.publisher.futures.Future, data: str
) -> Callable[[pubsub_v1.publisher.futures.Future], None]:
    def callback(publish_future: pubsub_v1.publisher.futures.Future) -> None:
        try:
            print(publish_future.result(timeout=60))
        except futures.TimeoutError:
            print(f"Publishing {data} timed out.")

    return callback


def publish_message(messages: list[str], project_id: str, topic_id: str) -> None:
    """Publishes multiple messages to a Pub/Sub topic with an error handler."""

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    publish_futures = []

    for data in messages:
        publish_future = publisher.publish(topic_path, json.dumps(data).encode("utf-8"))
        publish_future.add_done_callback(get_callback(publish_future, data))
        publish_futures.append(publish_future)

    # Wait for all the publish futures to resolve before exiting.
    futures.wait(publish_futures, return_when=futures.ALL_COMPLETED)

    print(f"Published messages with error handler to {topic_path}.")


def run(project_id: str, topic_id: str, csv_path: str):
    messages = read_csv(file_path=csv_path)

    publish_message(messages=messages, project_id=project_id, topic_id=topic_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", dest="project", required=True)
    parser.add_argument("--topic", dest="topic", required=True)
    parser.add_argument("--csv-path", dest="csv_path", required=True)

    args = parser.parse_args()

    project_id = args.project  # "customermod-genai-sa"
    topic_id = args.topic  # "rdm-topic"
    csv_path = args.csv_path  # ""

    run(project_id=project_id, topic_id=topic_id, csv_path=csv_path)
