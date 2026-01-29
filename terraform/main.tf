terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.17.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_artifact_registry_repository" "latam_repo" {
  location      = var.region
  repository_id = "latam-challenge"
  description   = "Docker repository for LATAM challenge"
  format        = "DOCKER"
}

resource "google_cloud_run_v2_service" "latam_api" {
  name                = var.service_name
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.latam_repo.repository_id}/latam_api:latest"
      ports {
        container_port = 8080
      }
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_v2_service_iam_policy" "policy" {
  project  = google_cloud_run_v2_service.latam_api.project
  location = google_cloud_run_v2_service.latam_api.location
  name     = google_cloud_run_v2_service.latam_api.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
