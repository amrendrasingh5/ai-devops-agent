from agent.investigator import investigate_pod, analyze_with_llm


class DevOpsAgent:
    """
    Read-only AI DevOps agent for Kubernetes investigation.
    """

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
