# Configure the Google Cloud provider
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "your-project-id"
  region  = "us-central1"
}

# Create a Firestore Database and collection
resource "google_firestore_document" "default" {
  collection = "shared-retail-demos-firestore"
  document_id = "__initial-setup-doc__"

  fields = {
    config = {
      fields = {
        customerName = {
          string_value = ""
        }
      }
    }
    date = {
      number_value = "1725514849320"
    }
    country = {
      string_value = "USA"
    }
  }
}

# Create a Google Cloud Storage bucket
resource "google_storage_bucket" "default" {
  name          = "your-bucket-name"
  location      = "US"
  force_destroy = true
}

# Create App Engine application
resource "google_app_engine_application" "app" {
}

# Create a service account for the App Engine application
resource "google_service_account" "default" {
  account_id   = "your-service-account-name"
  display_name = "App Engine default service account"
}

# Grant the service account read/write access to the bucket
resource "google_storage_bucket_iam_member" "member" {
  bucket = google_storage_bucket.default.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.default.email}" 1 
}

# Enable the Vertex AI API
resource "google_project_service_identity" "vertex_ai_api" {
  service  = "aiplatform.googleapis.com"
  provider = google
}

# Enable the Gemini API
resource "google_project_service_identity" "gemini_api" {
  service  = "gemini.googleapis.com"
  provider = google
}

# Create an application token for accessing Gemini
resource "google_service_account_access_token" "gemini_token" {
  target_service_account = google_service_account.default.name
  scopes                = ["https://www.googleapis.com/auth/cloud-platform"]
  lifetime               = "3600s" # Token expires in 1 hour
}

# Deploy the default service
resource "google_app_engine_standard_app_version" "default" {
  version_id = "default"
  service    = "default"
  runtime    = "nodejs22"

  entrypoint {
    shell = "node dist/apps/demo/main.js" # Replace with your main script
  }

  deployment {
    zip {
      source_url = "your-default-service-source-url" # Replace with your source code URL
    }
  }

  noop_on_destroy = true
}

# Deploy the API service
resource "google_app_engine_standard_app_version" "api" {
  version_id = "api"
  service    = "api"
  runtime    = "nodejs22"

  entrypoint {
    shell = "node dist/apps/api/main.js" # Replace with your API script
  }

  deployment {
    zip {
      source_url = "your-api-service-source-url" # Replace with your source code URL
    }
  }

  noop_on_destroy = true
}

# Configure dispatch.yaml
resource "google_app_engine_application_url_dispatch_rules" "dispatch" {
  dispatch_rules {
    domain  = "*"
    path    = "/"
    service = google_app_engine_standard_app_version.default.service
  }

  dispatch_rules {
    domain  = "*"
    path    = "/api/*"
    service = google_app_engine_standard_app_version.api.service
  }
}