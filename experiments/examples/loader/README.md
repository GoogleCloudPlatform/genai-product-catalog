# Data Loader

## Introduction

The Data Loader uses Dataflow to process and load the data to prepare your catalog to start using the GenAI based features offered by this solution.

We use `Dataflow` and `Pub/Sub` to run this pipeline. The following steps illustrate the entire workflow for the pipeline.

## Prerequisites for the pipeline

1. Create a BigQuery table to store the Retail Data Model transformed dataset along with the embeddings

```sql
CREATE TABLE `<PROJECT_ID>.<DATASET_ID>.<TABLE_ID>`
(
  business_keys ARRAY<STRUCT<value STRING, name STRING>>,
  image_embedding ARRAY<FLOAT64>,
  text_embedding ARRAY<FLOAT64>,
  categories ARRAY<STRUCT<children ARRAY<STRUCT<children ARRAY<STRUCT<children ARRAY<STRUCT<children ARRAY<STRING>, name STRING, id STRING>>, name STRING, id STRING>>, name STRING, id STRING>>, name STRING, id STRING>>,
  base_price STRUCT<rounding_rule STRUCT<trim_insignificant_digits BOOL, relevant_decimal INT64>, value STRUCT<decimal INT64, whole INT64>, code STRING>,
  headers ARRAY<STRUCT<attribute_values ARRAY<STRING>, images ARRAY<STRUCT<url STRING, origin_url STRING>>, nlp_description STRING, locale STRING, long_description STRING, short_description STRING, brand STRING, name STRING>>
);
```

2. Place a CSV record of your product dataset under `/applied-ai/third_party/flipkart`

3. Create a GCS bucket with your `<BUCKET_NAME>` to store various metadata and images, etc.

4. Create a folder inside GCS named `dataflow` and upload the local file `streaming-beam.json` to that folder

5. Create a [Pub/Sub topic](https://cloud.google.com/pubsub/docs/create-topic#create_a_topic_2) and [subscription](https://cloud.google.com/pubsub/docs/create-subscription#create_a_pull_subscription) to publish messages (rows of data) and subscription to trigger the dataflow processing job. 

6. Remeber to keep track of the IDs of the resources created above to plug into the code snippets below.

## Create Dataflow Pipeline

The follwing steps illustrate how you can run the data procesing pipeline in various scenarios.


1. Build Container Image

```shell
export PROJECT=<PROJECT_ID>
export TEMPLATE_IMAGE="gcr.io/$PROJECT/dataflow/streaming-beam:latest"
gcloud builds submit --project $PROJECT --tag "$TEMPLATE_IMAGE" .
```

2. Build the Dataflow Flex template to run the pipeline

```shell
export BUCKET=<BUCKET_NAME>
export TEMPLATE_PATH="gs://$BUCKET/dataflow/templates/streaming-beam.json"

# Build the Flex Template.
gcloud dataflow flex-template build $TEMPLATE_PATH \
  --image "$TEMPLATE_IMAGE" \
  --sdk-language "PYTHON" \
  --metadata-file "metadata.json"
```

3. Submit the job to Google Cloud Dataflow Runner

```shell
export REGION="us-central1"

gcloud dataflow flex-template run "streaming-beam-<JOB_ID>-`date +%Y%m%d-%H%M%S`" \
    --template-file-gcs-location "$TEMPLATE_PATH" \
    --temp-location gs://<GCS_LOGS_BUCKET_NAME>/tmp/ \
    --project $PROJECT \
    --parameters input_subscription="projects/${PROJECT}/subscriptions/<SUBSCRIPTION_NAME>" \
    --parameters bucket="<BUCKET_NAME>" \
    --parameters bq-table-id="<DATASET_ID>.<TABLE_ID >" \
    --enable-streaming-engine \
    --region "$REGION"
```

4. [OPTIONAL] For local testing, you can use DirectRunner

```shell
python -m dataflow_loader \
    --region "${REGION}" \
    --runner DirectRunner \
    --project "${PROJECT}" \
    --input_subscription="projects/${PROJECT}/subscriptions/<SUBSCRIPTION_NAME>" \
    --bucket="${BUCKET}" \
    --bq-table-id="<DATASET_ID>.<TABLE_ID>" \
    --streaming \
    --temp-location gs://<GCS_LOGS_BUCKET_NAME>/tmp/
```

5. Run the python script to publish the dataset rows to `Pub/Sub`
```shell
 python3 publish_csv.py \
    --project=$PROJECT_ID \
    --topic=$TOPIC_NAME \
    --csv-path=$CSV_DATASET_PATH
```

Once the dataflow pipeline has completed, you can continue to the next section to prepare the data for ingestion into `Vertex Vector Search`

## Data Preparation in BigQuery

1. Create a new table (or drop records in existing table) without duplicate rows that may have been written from Dataflow. This is a bit tricky as our catalog contains complex STRUCT. We willr refer to this table as `DEDUP_TABLE_ID`

```sql
WITH RankedData AS (
  SELECT
    *,
    ROW_NUMBER() OVER(PARTITION BY business_keys[OFFSET(0)].value ORDER BY business_keys[OFFSET(0)].value) AS rn
  FROM
    `<PROJECT_ID>.<DATASET_ID>.<TABLE_ID>`
)

SELECT
  *
FROM
  RankedData
WHERE
  rn = 1
```

2. Since Vertex Vector Search can only take an input in JSONL in the structure of `{"id": "<product_id>", "embedding": "embedding_value"}`, we need to create a new table to extract JSONL data from in this structure.

```sql
SELECT CONCAT(business_keys[1].value, "_T") as id, text_embedding as embedding
FROM `<PROJECT_ID>.<DATASET_ID>.<DEDUP_TABLE_ID>`
WHERE business_keys[1].name = "OID"
UNION ALL
SELECT CONCAT(business_keys[1].value, "_I") as id, image_embedding as embedding
FROM `<PROJECT_ID>.<DATASET_ID>.<DEDUP_TABLE_ID>`
WHERE business_keys[1].name = "OID"
```
We have now concatenated our ID with a `_T` or `_I` to indicate whether it is a text or an image embedding respectively.

3. Save the results of the query from Step (2) as JSONL. Download the file and upload it to a GCS bucket

4.  [Setup a Vertex Vector Search Index](https://cloud.google.com/vertex-ai/docs/vector-search/create-manage-index) and point the index to the GCS bucket from Step (3). This step usually takes about an hour or so as we need to build the index from scratch.

5. Flatten the deduplicated table and create a new table from this `` so that we can utilize it in our downstream services and notebooks provided as part of the `examples`.

```sql
SELECT
  business_keys[1].value as id,
  headers[0].long_description as description,
  categories[0].name AS c0_name,
  child1.name AS c1_name,
  child2.name AS c2_name,
  child3.name AS c3_name,
  headers[0].images[0].url as url,
  CONCAT(
    '{', 
    STRING_AGG(
      CONCAT(
        '"', 
        JSON_EXTRACT_SCALAR(TO_JSON_STRING(attribute_value), '$.template_attribute_rule.name'), 
        '": "', 
        JSON_EXTRACT_SCALAR(TO_JSON_STRING(attribute_value), '$.string_value'), 
        '"'
      ), 
      ','
    ), 
    '}'
  ) AS attributes
FROM `<PROJECT_ID>.<DATASET_ID>.<DEDUP_TABLE_ID>`
LEFT JOIN UNNEST(categories) AS category
LEFT JOIN UNNEST(category.children) AS child1
LEFT JOIN UNNEST(child1.children) AS child2
LEFT JOIN UNNEST(child2.children) AS child3
LEFT JOIN UNNEST(headers) as header
LEFT JOIN UNNEST(header.attribute_values) AS attribute_value
GROUP BY 1,2,3,4,5,6,7
```

6. Congrats! We have now mapped your dataset into our standard format. You can now plug in this table and all the empty variable in the `conf/app.toml` file to start running all your services.