# Copyright 2023 Google LLC
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

module "product_rdm_topic" {
  project_id = var.gcp_project_id
  source     = "terraform-google-modules/pubsub/google"
  topic      = "product_info_rdm"
  version    = "6.0.0"

  message_storage_policy = {
    allowed_persistence_regions = [
      var.gcp_default_region
    ]
  }

  pull_subscriptions = [
    {
      name                         = "product_info_rdm-sub"
      ack_deadline_seconds         = 10
    },
  ]

  depends_on = [
    google_project_service.google-cloud-apis
  ]
}
