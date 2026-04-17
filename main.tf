provider "google" {
  project = "currency-prices-data-pipeline"
  region  = "europe-central2"
}

data "google_project" "project" {}

resource "google_artifact_registry_repository" "nbp_repo" {
  project       = "currency-prices-data-pipeline"
  location      = "europe-central2"
  repository_id = "nbp-app-repo"
  format        = "DOCKER"
}

resource "google_storage_bucket" "nbp_data_lake" {
  name          = "nbp-data-lake-${var.project_id}"
  location      = "EUROPE-CENTRAL2"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_cloud_run_v2_service" "nbp_service" {
  name                = "nbp-api"
  location            = "europe-central2"
  deletion_protection = false

  template {
    containers {
      image = "europe-central2-docker.pkg.dev/${var.project_id}/nbp-app-repo/nbp-app:latest"
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      env {
        name  = "BUCKET_NAME"
        value = google_storage_bucket.nbp_data_lake.name
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_binding" "public" {
  name     = google_cloud_run_v2_service.nbp_service.name
  location = google_cloud_run_v2_service.nbp_service.location
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}

resource "google_storage_bucket_iam_member" "run_storage_writer" {
  bucket = google_storage_bucket.nbp_data_lake.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_service" "scheduler_api" {
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

resource "google_cloud_scheduler_job" "nbp_job" {
  name             = "nbp-daily-ingest"
  description      = "Downloading data and write them in GCS"
  schedule         = "0 9 * * *"
  time_zone        = "Europe/Warsaw"
  attempt_deadline = "320s"

  http_target {
    http_method = "GET"
    uri         = google_cloud_run_v2_service.nbp_service.uri
  }

  depends_on = [google_project_service.scheduler_api]
}

resource "google_bigquery_dataset" "nbp_dataset" {
  dataset_id = "nbp_analytics"
  location   = "europe-west1"
}

resource "google_bigquery_table" "nbp_external_table" {
  dataset_id = google_bigquery_dataset.nbp_dataset.dataset_id
  table_id   = "exchange_rates_raw"

  external_data_configuration {
    autodetect    = false
    source_format = "NEWLINE_DELIMITED_JSON"
    source_uris   = ["gs://${google_storage_bucket.nbp_data_lake.name}/*.json"]
  }

  schema = <<EOF
[
  {
    "name": "table",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "no",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "effectiveDate",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "rates",
    "type": "RECORD",
    "mode": "REPEATED",
    "fields": [
      {
        "name": "currency",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "code",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "mid",
        "type": "FLOAT",
        "mode": "NULLABLE"
      }
    ]
  }
]
EOF
}

#tu wlaczamy uslugi polaczen bugquery i aiplatform
resource "google_project_service" "services" {
  for_each = toset([
    "bigqueryconnection.googleapis.com",
    "aiplatform.googleapis.com"
  ])
  service = each.key
}

#tworzenie polaczenia bigquery <-> vertex ai
resource "google_bigquery_connection" "vertex_ai_conn" {
  connection_id = "vertex-ai-connection"
  project       = var.project_id
  location      = "europe-west1"
  cloud_resource {}
}

#nadanie polaczenie dla service account ktore bedzie mialo dostep do vertex ai
resource "google_project_iam_member" "connection_permission" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_bigquery_connection.vertex_ai_conn.cloud_resource[0].service_account_id}" #interpolacja
}

