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
  name     = "nbp-api"
  location = "europe-central2"
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