from agent.investigator import (
    investigate_pod,
    analyze_with_llm,
    find_pods,
)

from agent.request import understand_request

class DevOpsAgent:
    """
    Read-only AI DevOps agent for Kubernetes investigation.
    """

    def __init__(self):
        """
        Store conversational context for the current session.
        """

        self.last_candidates = []

    def discover_unhealthy_pods(self, namespace: str | None = None):
        """
        Discover unhealthy Kubernetes pods.

        If namespace is None, search all namespaces.       

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


    def handle_request(self, request: str):
        """
        Handle a natural-language DevOps investigation request.

        This method is currently read-only.
        """

        print(f"\nUser request: {request}")

        # ---------------------------------------------------------
        # Handle conversational references
        # ---------------------------------------------------------

        request_lower = request.lower().strip()

        if self.last_candidates:

            if request_lower in {
                "the first one",
                "first one",
                "the first pod",
                "first pod",
            }:

                pod = self.last_candidates[0]

                print(
                    f"\n[AGENT] You selected: "
                    f"{pod['namespace']}/{pod['name']}"
                )

                return self.investigate(
                    pod_name=pod["name"],
                    namespace=pod["namespace"],
                )

            if request_lower in {
                "the second one",
                "second one",
                "the second pod",
                "second pod",
            } and len(self.last_candidates) >= 2:

                pod = self.last_candidates[1]

                print(
                    f"\n[AGENT] You selected: "
                    f"{pod['namespace']}/{pod['name']}"
                )

                return self.investigate(
                    pod_name=pod["name"],
                    namespace=pod["namespace"],
                )


        # ---------------------------------------------------------
        # Step 1: Understand the user's request
        # ---------------------------------------------------------

        devops_request = understand_request(request)

        print("\n[AGENT] Understanding request...")

        print(
            f"[AGENT] Intent: "
            f"{devops_request.intent}"
        )

        print(
            f"[AGENT] Resource type: "
            f"{devops_request.resource_type}"
        )

        print(
            f"[AGENT] Resource name: "
            f"{devops_request.resource_name}"
        )

        # ---------------------------------------------------------
        # Step 2: Validate supported request
        # ---------------------------------------------------------

        if (
            devops_request.intent != "investigate"
            or devops_request.resource_type != "pod"
        ):
            print(
                "\n[AGENT] I currently support "
                "Kubernetes pod investigation."
            )

            return devops_request

        # ---------------------------------------------------------
        # Step 3: User specified a pod
        # ---------------------------------------------------------

        if devops_request.resource_name:

            print(
                f"\n[AGENT] Looking for pod: "
                f"{devops_request.resource_name}"
            )

            pods = find_pods(
                namespace=devops_request.namespace,
                health=None,
            )

            matching_pods = [
                pod
                for pod in pods
                if pod["name"].lower()
                == devops_request.resource_name.lower()
            ]

            if len(matching_pods) == 1:

                pod = matching_pods[0]

                print(
                    f"[AGENT] Found: "
                    f"{pod['namespace']}/{pod['name']}"
                )

                return self.investigate(
                    pod_name=pod["name"],
                    namespace=pod["namespace"],
                )

            if not matching_pods:

                print(
                    f"\n[AGENT] Pod "
                    f"'{devops_request.resource_name}' "
                    "was not found."
                )

                return []

        # ---------------------------------------------------------
        # Step 4: User did not specify a pod
        # ---------------------------------------------------------

        print(
            "\n[AGENT] No specific pod was named."
        )

        print(
            "[AGENT] Discovering unhealthy pods..."
        )

        pods = find_pods(
            namespace=devops_request.namespace,
            health="unhealthy",
        )

        # ---------------------------------------------------------
        # Step 5: No unhealthy pods
        # ---------------------------------------------------------

        if not pods:

            print(
                "[AGENT] No unhealthy pods are "
                "currently detected."
            )

            return []
        
        self.last_candidates = pods

        # ---------------------------------------------------------
        # Step 6: Exactly one unhealthy pod
        # ---------------------------------------------------------

        if len(pods) == 1:

            pod = pods[0]

            print(
                f"[AGENT] Only one unhealthy pod found: "
                f"{pod['namespace']}/{pod['name']}"
            )

            return self.investigate(
                pod_name=pod["name"],
                namespace=pod["namespace"],
            )

        # ---------------------------------------------------------
        # Step 7: Multiple unhealthy pods
        # ---------------------------------------------------------

        print(
            f"\n[AGENT] Found {len(pods)} unhealthy pods."
        )

        print(
            "[AGENT] Please specify which pod "
            "you want me to investigate:"
        )

        for pod in pods:
            print(
                f"  - {pod['namespace']}/{pod['name']}"
            )

        return pods

    def investigate_unhealthy_pods(self):
        """
        Discover unhealthy pods across the cluster and investigate them.

        This workflow is read-only.
        """

        pods = self.discover_unhealthy_pods()

        if not pods:
            print("\n[AGENT] No unhealthy pods are currently detected.")
            return []

        results = []

        for pod in pods:
            result = self.investigate(
                pod_name=pod["name"],
                namespace=pod["namespace"],
            )

            results.append(result)

        return results

    def investigate(self, pod_name: str, namespace: str = "default"):
        """
        Investigate a Kubernetes pod and analyze the collected evidence.
        """

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
