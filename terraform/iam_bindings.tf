resource "google_project_iam_member" "gke_sa_artifact_reader" {
  project = "eventflow-tibame-2026"
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.eventflow_gke_sa.email}"
}
