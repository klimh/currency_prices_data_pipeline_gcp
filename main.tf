provider "google" {
  project = "currency-prices-data-pipeline"
  region  = "europe-central2"
}

resource "google_artifact_registry_repository" "nbp_repo" {
  project       = "currency-prices-data-pipeline"
  location      = "europe-central2"
  repository_id = "nbp-app-repo"
  format        = "DOCKER"
}

resource "google_cloud_run_v2_service" "nbp_service" {
  name     = "nbp-api"
  location = "europe-central2"

  template {
    containers {
      image = "europe-central2-docker.pkg.dev/${var.project_id}/nbp-app-repo/nbp-app:latest"
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
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