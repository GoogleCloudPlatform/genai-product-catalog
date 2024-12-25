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

# The default dataflow job runner service account
locals {
  compute_engine_service_account = "${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Dataflow Accessing Pub/Sub: 
# * https://cloud.google.com/dataflow/docs/concepts/security-and-permissions#accessing_pubsub
resource "google_project_iam_member" "viai-cloud-deploy-serviceAccountUser" {
  project = var.gcp_project_id

  for_each = toset([
    "roles/bigquery.admin",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/dataflow.worker",
    "roles/discoveryengine.viewer",
    "roles/logging.logWriter",
    "roles/pubsub.editor",
    "roles/pubsub.subscriber",
    "roles/pubsub.viewer",
    "roles/storage.admin",
    "roles/storage.objectViewer",
    "roles/aiplatform.user"
  ])
  role   = each.key
  member = "serviceAccount:${local.compute_engine_service_account}"
  depends_on = [
    google_project_service.google-cloud-apis
  ]
}
