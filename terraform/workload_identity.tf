resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.eventflow_gke_sa.name
  role                = "roles/iam.workloadIdentityUser"
  member              = "serviceAccount:eventflow-tibame-2026.svc.id.goog[default/eventflow-ksa]"

  depends_on = [google_container_cluster.eventflow]
}
