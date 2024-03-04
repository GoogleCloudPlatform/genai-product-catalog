# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

output "pubsub_subscription_id" {
  description = "Pub/Sub Subscription Id"
  value       = module.product_rdm_topic.subscription_paths[0]
}

output "bigquery_product-info" {
  description = "Pub/Sub Subscription Id"
  value       = "${module.product-info.bigquery_dataset.dataset_id}.${module.product-info.table_ids[0]}"
}

output "dataflow_bucket_name" {
    description = "Bucket name for Dataflow Jobs"
    value       = module.dataflow_bucket.name
}

output "google_vertex_ai_index_endpoint_id" {
    description = "Deployed Index Id"
    value       = google_vertex_ai_index_endpoint.index_endpoint.id
}

output "google_vertex_ai_index_endpoint_public_url" {
    description = "Deployed Index Public Domain Name"
    value       = google_vertex_ai_index_endpoint.index_endpoint.public_endpoint_domain_name
}

output "notice" {
  value = <<EOF
=========================================================================
Index deployment job submitted, it can take up to 60 minutes to complete.
=========================================================================
EOF
}
