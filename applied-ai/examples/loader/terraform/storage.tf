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

module "dataflow_bucket" {
  location = var.gcp_default_region
  names = [
    "${var.gcp_project_id}_dataflow_bucket"
  ]
  project_id       = var.gcp_project_id
  prefix           = ""
  randomize_suffix = false
  source           = "terraform-google-modules/cloud-storage/google"
  version          = "5.0.0"
  force_destroy = {
    ("${var.gcp_project_id}_dataflow_bucket") = true
  }

  depends_on = [
    google_project_service.google-cloud-apis
  ]
}