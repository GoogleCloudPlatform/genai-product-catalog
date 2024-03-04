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

# Create Index
module "vector_search_index_bucket" {
  location = var.gcp_default_region
  names = [
    "${var.gcp_project_id}_vector_search_bucket"
  ]
  project_id       = var.gcp_project_id
  prefix           = ""
  randomize_suffix = false
  source           = "terraform-google-modules/cloud-storage/google"
  version          = "5.0.0"
  force_destroy = {
    ("${var.gcp_project_id}_vector_search_bucket") = true
  }

  depends_on = [
    google_project_service.google-cloud-apis
  ]
}

resource "google_storage_bucket_object" "vector_search_init" {
  name   = "contents/data.json"
  bucket = module.vector_search_index_bucket.name
  content = file("./files/vector_search_init.jsonl")
}

resource "google_vertex_ai_index" "index" {
  region   = var.gcp_default_region
  display_name = "${var.gcp_project_id}_product_index"
  description = "${var.gcp_project_id} Product Catalog Index"
  metadata {
    contents_delta_uri = "gs://${module.vector_search_index_bucket.name}/contents"
    config {
      dimensions = 1408
      approximate_neighbors_count = 150
      shard_size = "SHARD_SIZE_SMALL"
      distance_measure_type = "COSINE_DISTANCE"
      feature_norm_type = "UNIT_L2_NORM"  # Must be UNIT_L2_NORM if distance_measure_type is COSINE_DISTANCE
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 1000  # Default
          leaf_nodes_to_search_percent = 10  # Default
        }
      }
    }
  }
  index_update_method = "BATCH_UPDATE"
}

# Create Endpoint
resource "google_vertex_ai_index_endpoint" "index_endpoint" {
  display_name = "product-catalog-index-endpoint"
  description  = "Product Catalog Index Endpoint"
  region       = var.gcp_default_region
  # If public_endpoint_enabled is set to True, network cannot be specified.
  # network      = "projects/${data.google_project.project.number}/global/networks/${google_compute_network.default.name}"
  public_endpoint_enabled = true
  depends_on   = [
    google_service_networking_connection.vertex_vpc_connection
  ]
}

resource "google_service_networking_connection" "vertex_vpc_connection" {
  network                 = google_compute_network.default.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.vertex_range.name]
}

resource "google_compute_global_address" "vertex_range" {
  name          = "address-name"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 24
  network       = google_compute_network.default.id
}

# Deploy Index to Endpoint
# * Note  : Terraform does not currently support deploy index endpoint via Terraform modules
# * Issue : https://github.com/hashicorp/terraform-provider-google/issues/12818
module "gcloud_ai_index_endpoints_deploy_index" {
  source  = "terraform-google-modules/gcloud/google"
  version = "3.4.0"

  create_cmd_body  = "ai index-endpoints deploy-index ${google_vertex_ai_index_endpoint.index_endpoint.id} --deployed-index-id=deployed_index --display-name=deployed_index --index=${google_vertex_ai_index.index.id} --project=${var.gcp_project_id} --region=${var.gcp_default_region}"
  destroy_cmd_body = "ai index-endpoints undeploy-index ${google_vertex_ai_index_endpoint.index_endpoint.id} --deployed-index-id=deployed_index --project=${var.gcp_project_id} --region=${var.gcp_default_region}"

  depends_on = [
    google_vertex_ai_index_endpoint.index_endpoint,
    google_storage_bucket_object.vector_search_init
  ]
}