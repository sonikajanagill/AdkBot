variable "project" {}

resource "google_service_account" "agent_sa" {
  account_id   = "clawdbot-runtime"
  display_name = "ClawdBot Agent Runtime Service Account"
  project      = var.project
}

# Grant basic required roles
resource "google_project_iam_member" "datastore" {
  project = var.project
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "trace" {
  project = var.project
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "dlp" {
  project = var.project
  role    = "roles/dlp.user"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

output "service_account_email" {
  value = google_service_account.agent_sa.email
}
