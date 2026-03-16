variable "project" {}
variable "secrets" {
  type = map(string)
}

resource "google_secret_manager_secret" "agent_secrets" {
  for_each  = var.secrets
  secret_id = each.key
  project   = var.project

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "agent_secret_versions" {
  for_each    = var.secrets
  secret      = google_secret_manager_secret.agent_secrets[each.key].id
  secret_data = each.value
}

output "secret_ids" {
  value = [for s in google_secret_manager_secret.agent_secrets : s.id]
}
