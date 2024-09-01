# Provision Cloud Resources

## Preparation

Create `variables.tfvars` in [example/loader/terraform](./terraform/) folder, the file must have the following foramt

```ini
gcp_default_region="<DEFAULT GCP REGION - ex:us-central1>"
gcp_project_id="<GCP PROJECT ID>"
```

## Provision Cloud Resources

```shell
cd examples/loader/terraform

terraform init
terraform apply -var-file=./variables.tfvars
```

Once complet, you will see outputs of provisioned cloud resources, note down the outputs.

```shell
bigquery_product-info = "products.product_info"
dataflow_bucket_name = "<GCP PROJECT ID>_dataflow_bucket"
pubsub_subscription_id = "projects/<GCP PROJECT ID>/subscriptions/product_info_rdm-sub"
```

The Terraform provisions the following resources:

* BigQuery dataset.

* Cloud Storage Bucket.

* VPC Network and Firewall.

* Pub/Sub topic and subscription.

* Grant required roles to default Dataflow Job service account.
