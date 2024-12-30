# Configure the Google Cloud provider

variable "project_name" {}
variable "region" {}
variable "tier" { type = string }
variable "pwd" { type = string }

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_name
  region  = var.region
}

resource "google_sql_database" "main" {
  name     = "gcp-genai-catalog"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_database_instance" "main" {
  name             = "gcp-genai-catalog"
  database_version = "POSTGRES_17"
  region           = var.region
  settings {
    # Second-generation instance tiers are based on the machine
    # type. See argument reference below.
    tier = var.tier
  }
}

resource "google_sql_user" "owner_user" {
  name     = "gcp-genai-catalog"
  instance = google_sql_database_instance.main.name
  password = var.pwd # Use a strong password
}

# resource "null_resource" "install_pgvector" {
#   provisioner "remote-exec" {
#     inline = [
#       "psql -h localhost -p 5432 -U gcp-genai-catalog -d gcp-genai-catalog -c 'CREATE EXTENSION IF NOT EXISTS vector;'",
#     ]
#   }
#   depends_on = [google_sql_database_instance.main]
# }

