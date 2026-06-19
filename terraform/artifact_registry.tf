resource "google_artifact_registry_repository" "eventflow" {
  location      = "asia-east1"
  repository_id = "eventflow-repo"
  description   = "EventFlow 微服務 image 倉庫"
  format        = "DOCKER"

  depends_on = [google_project_service.artifactregistry]
}
