from agent.investigator import (
    investigate_pod,
    analyze_with_llm,
    find_pods,
)

class DevOpsAgent:
    """
    Read-only AI DevOps agent for Kubernetes investigation.
    """

    def discover_unhealthy_pods(self, namespace: str = "default"):
        """
        Discover unhealthy Kubernetes pods.

        This function is read-only.
        """

        print("\n[AGENT] Discovering unhealthy pods...")

        pods = find_pods(
            namespace=namespace,
            health="unhealthy",
        )

        if not pods:
            print("[AGENT] No unhealthy pods found.")
            return []

        print(f"[AGENT] Found {len(pods)} unhealthy pod(s).")

        for pod in pods:
            print(f"  - {pod['name']}")

        return pods
    def investigate(self, pod_name: str, namespace: str = "default"):
        """
        Investigate a Kubernetes pod and analyze the collected evidence.
        """

        print("\n================================")
        print("AI DEVOPS AGENT")
        print("================================")

        print(f"\nPod: {pod_name}")
        print(f"Namespace: {namespace}")

        print("\n[AGENT] Collecting Kubernetes evidence...")

        investigation = investigate_pod(
            pod_name=pod_name,
            namespace=namespace,
        )

        if "error" in investigation:
            print(f"\n[ERROR] {investigation['error']}")
            return investigation

        print("[AGENT] Evidence collected.")

        print("\n[AGENT] Analyzing evidence with AI...")

        analysis = analyze_with_llm(investigation)

        print("\n================================")
        print("AI ANALYSIS")
        print("================================")
        print(analysis)

        return {
            "investigation": investigation,
            "analysis": analysis,
        }
