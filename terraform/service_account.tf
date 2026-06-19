resource "google_service_account" "eventflow_gke_sa" {
  account_id   = "eventflow-gke-sa"
  display_name = "EventFlow GKE Workload Service Account"
  description  = "GKE Pod 用來存取 Artifact Registry 的身份"

  depends_on = [google_project_service.iam]
}
