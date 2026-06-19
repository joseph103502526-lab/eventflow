resource "google_container_cluster" "eventflow" {
  name     = "eventflow-cluster"
  location = "asia-east1"

  enable_autopilot = true

  workload_identity_config {
    workload_pool = "eventflow-tibame-2026.svc.id.goog"
  }

  deletion_protection = false

  depends_on = [google_project_service.container]
}
