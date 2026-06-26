"""
EventFlow — GKE 微服務平台 架構圖 (5.1 Level 1) - 修正版
執行: pip install diagrams && python eventflow_arch_diagram.py
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.gcp.compute import GKE, KubernetesEngine
from diagrams.gcp.devtools import ContainerRegistry
from diagrams.gcp.security import Iam
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Ingress
from diagrams.k8s.ecosystem import Helm
from diagrams.k8s.rbac import ServiceAccount
from diagrams.onprem.ci import Jenkins
from diagrams.onprem.monitoring import Prometheus, Grafana, PrometheusOperator
from diagrams.onprem.client import User
from diagrams.onprem.vcs import Github

# 全局圖表屬性（修正：移除巢狀 dict，只留純字串屬性）
graph_attr = {
    "fontsize": "22",           # 放大最外面大標題的字體
    "bgcolor": "#FFFFFF",       # 純白乾淨底色
    "pad": "0.8",
    "splines": "ortho",
    "nodesep": "0.9",           # 拉開上下節點間距
    "ranksep": "1.3",           # 拉開左右層級間距
}

# 單獨定義節點屬性字典，直接帶入 Diagram 參數中
node_attr = {
    "fontsize": "15",           # 保持放大的字體
    "labelloc": "b",            # 強制將 Label（文字）放在節點底部
    "height": "1.3",            # 稍微加高節點的容器（預設通常是 0.5~1.0），幫文字預留向下延展的空間
}

with Diagram(
    "EventFlow Microservices Platform — GKE Architecture",
    filename="eventflow_architecture",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,         # <-- 修正：改從這裡傳入
):
    client = User("Client\n(Browser/curl)")

    # 1. 本地開發與 CI/CD 區塊
    with Cluster("WSL2 — Ubuntu", graph_attr={"bgcolor": "#F4F6F8", "pencolor": "#CFD8DC", "fontsize": "16"}):
        github = Github("GitHub\n(ngrok webhook)")
        jenkins = Jenkins("Jenkins CI/CD\nBuild #24")
        mcp = Prometheus("AIOps\nMCP Server\n(FastMCP)")

    # 2. GCP 雲端最外層環境
    with Cluster("GCP asia-east1", graph_attr={"bgcolor": "#F8FAFC", "pencolor": "#94A3B8", "fontsize": "16"}):
        ar = ContainerRegistry("Artifact Registry\neventflow-repo")

        # IAM 區塊
        with Cluster("IAM / Workload Identity", graph_attr={"bgcolor": "#F1F5F9", "pencolor": "#CBD5E1", "fontsize": "15"}):
            gcp_sa = Iam("GCP SA\neventflow-gke-sa")
            wi_bind = Iam("Workload Identity\nBinding")

        # GKE 叢集主要環境
        with Cluster("GKE Autopilot — eventflow-cluster", graph_attr={"bgcolor": "#FFFFFF", "pencolor": "#475569", "labelloc": "t", "fontsize": "16"}):
            ingress = Ingress("GKE Ingress\nNEG + L7 LB")

            # 核心服務 Namespace
            with Cluster("default namespace", graph_attr={"bgcolor": "#E0F2FE", "pencolor": "#38BDF8", "fontsize": "16"}):
                gw  = Pod("api-gateway\nNode.js :3000")
                es  = Pod("event-service\nFlask :5001")
                bs  = Pod("booking-service\nFlask :5002")
                ns_ = Pod("notification-service\nFlask :5003")
                ksa = ServiceAccount("K8s SA\neventflow-ksa")
                helm = Helm("Helm Chart\n4 releases")
                keda = KubernetesEngine("KEDA ScaledObjects\n00:00→0 / 08:30→1\nevent-svc: +CPU 50%")

            # 監控運維 Namespace
            with Cluster("monitoring namespace", graph_attr={"bgcolor": "#F8FAFC", "pencolor": "#CBD5E1", "fontsize": "16"}):
                prom  = Prometheus("Prometheus\nServiceMonitor×1")
                graf  = Grafana("Grafana\nDashboard×1")
                alert = PrometheusOperator("AlertManager\nHighErrorRate Rule")

    # ==================== 線條與流向優化 ====================
    
    # CI/CD 路徑
    github >> Edge(label="push trigger", color="#475569", fontsize="14") >> jenkins
    jenkins >> Edge(label="docker push\n:BUILD_NUMBER", color="#475569", fontsize="14") >> ar
    jenkins >> Edge(label="helm upgrade\n--wait", color="#475569", fontsize="14") >> ingress
    ar >> Edge(style="dashed", label="image pull\nWorkload Identity", color="#64748B", fontsize="14") >> gw

    # 請求路徑
    client >> Edge(label="HTTP", color="#1E3A8A", fontsize="14") >> ingress
    ingress >> Edge(color="#1E3A8A") >> gw
    gw >> Edge(color="#1E3A8A") >> es
    gw >> Edge(color="#1E3A8A") >> bs
    gw >> Edge(color="#1E3A8A") >> ns_

    # Workload Identity
    gcp_sa >> Edge(color="#475569") >> wi_bind >> Edge(color="#475569") >> ksa
    ksa >> Edge(style="dashed", color="#475569") >> gw

    # Helm 管理
    helm >> Edge(style="dashed", color="#EA580C") >> gw
    helm >> Edge(style="dashed", color="#EA580C") >> es
    helm >> Edge(style="dashed", color="#EA580C") >> bs
    helm >> Edge(style="dashed", color="#EA580C") >> ns_

    # KEDA 自動擴縮
    keda >> Edge(style="dashed", label="scale", color="#16A34A", fontsize="14") >> es
    keda >> Edge(style="dashed", color="#16A34A") >> bs
    keda >> Edge(style="dashed", color="#16A34A") >> ns_
    keda >> Edge(style="dashed", color="#16A34A") >> gw

    # 可觀測性指標
    es  >> Edge(style="dashed", label="/metrics", color="#4F46E5", fontsize="14") >> prom
    bs  >> Edge(style="dashed", color="#4F46E5") >> prom
    ns_ >> Edge(style="dashed", color="#4F46E5") >> prom
    gw  >> Edge(style="dashed", color="#4F46E5") >> prom
    prom >> Edge(color="#4F46E5") >> graf
    prom >> Edge(color="#4F46E5") >> alert

    # AIOps MCP
    mcp >> Edge(style="dashed", label="port-forward :9090", color="#0F172A", fontsize="14") >> prom
    mcp >> Edge(style="dashed", label="K8s Events API", color="#0F172A", fontsize="14") >> keda

print("Done: eventflow_architecture.png")