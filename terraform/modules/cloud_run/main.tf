variable "project" {}
variable "region" {}
variable "environment" {}
variable "service_account_email" {}

resource "google_cloud_run_v2_service" "clawdbot" {
  name     = "clawdbot-${var.environment}"
  location = var.region
  project  = var.project
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.service_account_email
    
    scaling {
      max_instance_count = 1
      min_instance_count = 0
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" # Placeholder until CI pushes
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project
      }
      
      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project
  location = var.region
  name     = google_cloud_run_v2_service.clawdbot.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_v2_service.clawdbot.uri
}
