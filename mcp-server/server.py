import json
import subprocess
import requests
from datetime import datetime, timedelta, timezone
from mcp.server.fastmcp import FastMCP
from kubernetes import client, config

mcp = FastMCP("eventflow-aiops")


@mcp.tool()
def get_gcp_billing(days: int = 7) -> str:
    """
    查詢 GCP 專案最近 N 天的費用狀況。
    透過 Cloud Billing API (Python SDK) 取得帳單帳戶與專案帳單狀態。
    """
    if days < 1 or days > 90:
        return json.dumps({"error": "days 必須介於 1 到 90 之間"})

    project_id = "eventflow-tibame-2026"

    try:
        import os
        os.environ["PATH"] = "/home/user1/google-cloud-sdk/bin:" + os.environ.get("PATH", "")

        from google.cloud import billing_v1

        billing_client = billing_v1.CloudBillingClient()

        project_billing_info = billing_client.get_project_billing_info(
            name=f"projects/{project_id}"
        )

        billing_account_name = project_billing_info.billing_account_name
        billing_enabled = project_billing_info.billing_enabled
        billing_account_id = billing_account_name.replace("billingAccounts/", "") if billing_account_name else "N/A"

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        console_url = (
            f"https://console.cloud.google.com/billing/{billing_account_id}"
            f"/reports?project={project_id}"
        )

        summary = {
            "project_id": project_id,
            "billing_account_id": billing_account_id,
            "billing_enabled": billing_enabled,
            "query_period": {
                "days": days,
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
            },
            "note": (
                "Cloud Billing API 提供帳單帳戶狀態查詢。"
                "實際費用金額需透過 GCP Console Billing Reports 取得，"
                "或設定 BigQuery Billing Export 後可用 SQL 查詢每日費用明細。"
            ),
            "console_billing_url": console_url,
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Billing API 查詢失敗: {str(e)}"})


@mcp.tool()
def query_prometheus(query: str) -> str:
    """
    對本機 Prometheus（localhost:9090）執行 PromQL 查詢。
    使用前請確認 port-forward 已開啟：
    kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
    """
    # 防呆：限制 query 長度避免過大查詢
    if len(query) > 500:
        return json.dumps({"error": "query 字串過長（上限 500 字元），請簡化查詢"})

    # 防呆：禁止明顯的高負載模式
    dangerous_patterns = ["[1y]", "[2y]", "[5y]"]
    for pattern in dangerous_patterns:
        if pattern in query:
            return json.dumps({"error": f"禁止使用超長時間範圍 {pattern}，請改用 [5m] 或 [1h]"})

    prometheus_url = "http://localhost:9090/api/v1/query"

    try:
        response = requests.get(
            prometheus_url,
            params={"query": query},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            return json.dumps({
                "error": "Prometheus 回傳非成功狀態",
                "detail": data
            })

        result = data.get("data", {}).get("result", [])

        # 整理輸出，讓 Claude 容易閱讀
        simplified = []
        for item in result:
            metric_labels = item.get("metric", {})
            value = item.get("value", [None, None])
            simplified.append({
                "labels": metric_labels,
                "timestamp": value[0],
                "value": value[1]
            })

        return json.dumps({
            "query": query,
            "result_count": len(simplified),
            "results": simplified
        }, ensure_ascii=False, indent=2)

    except requests.exceptions.ConnectionError:
        return json.dumps({
            "error": "無法連線到 Prometheus",
            "hint": "請確認 port-forward 已開啟：kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090"
        })
    except requests.exceptions.Timeout:
        return json.dumps({"error": "Prometheus 查詢逾時（10 秒），請簡化 query"})
    except Exception as e:
        return json.dumps({"error": f"未預期錯誤: {str(e)}"})


@mcp.tool()
def get_k8s_events_summary() -> str:
    """
    查詢 K8s default namespace 最近的 Events，
    特別標出 Warning 等級事件與 Pod 重啟記錄。
    """
    try:
        # 載入本機 kubeconfig（與 kubectl 使用同一份設定）
        import os
        os.environ["PATH"] = "/home/user1/google-cloud-sdk/bin:" + os.environ.get("PATH", "")
        config.load_kube_config()
        v1 = client.CoreV1Api()

        # 查詢 default namespace 的 events
        events = v1.list_namespaced_event(namespace="default")

        warning_events = []
        normal_events = []
        restart_events = []

        for event in events.items:
            event_info = {
                "name": event.metadata.name,
                "namespace": event.metadata.namespace,
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "involved_object": f"{event.involved_object.kind}/{event.involved_object.name}",
                "count": event.count,
                "last_timestamp": (
                    event.last_timestamp.isoformat()
                    if event.last_timestamp else None
                ),
            }

            if event.type == "Warning":
                warning_events.append(event_info)

            if event.reason in ["BackOff", "OOMKilling", "Killing",
                                 "Failed", "FailedScheduling", "Unhealthy"]:
                restart_events.append(event_info)
            elif event.type == "Normal":
                normal_events.append(event_info)

        # 只回傳最近 10 筆 normal events，warning 全部回傳
        summary = {
            "query_time": datetime.now(timezone.utc).isoformat(),
            "namespace": "default",
            "warning_events_count": len(warning_events),
            "warning_events": warning_events,
            "critical_reason_events": restart_events,
            "recent_normal_events": normal_events[-10:],
            "health_status": "HEALTHY" if len(warning_events) == 0 else "NEEDS_ATTENTION",
        }

        return json.dumps(summary, ensure_ascii=False, indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": f"K8s 查詢失敗: {str(e)}"})


if __name__ == "__main__":
    mcp.run()
