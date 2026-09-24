from agent.tools.kubernetes import (
    get_pods,
    get_pod_events,
    get_pod_logs,
    get_deployment,
    get_pod_deployment,
    find_pods,
)


def investigate_pod(
    pod_name: str,
    namespace: str = "default",
):
    """
    Collect Kubernetes evidence for investigating a pod.

    This function is read-only.
    """

    # 1. Get pod information
    pods = get_pods(namespace)

    pod = next(
        (item for item in pods if item["name"] == pod_name),
        None,
    )

    if pod is None:
        return {
            "error": f"Pod '{pod_name}' not found in namespace '{namespace}'"
        }

    # 2. Get pod events
    events = get_pod_events(
        pod_name,
        namespace,
    )

    # 3. Get pod logs
    logs = get_pod_logs(
        pod_name,
        namespace,
    )


    deployment_name = get_pod_deployment(
        pod_name,
        namespace,
    )

    deployment = None

    if deployment_name:
        deployment = get_deployment(
            deployment_name,
            namespace,
        )
    return {
        "pod": pod,
        "events": events,
        "logs": logs,
        "deployment": deployment,
    }

def summarize_investigation(investigation):
    """
    Convert investigation evidence into a human-readable summary.

    This function does not modify Kubernetes resources.
    """

    if "error" in investigation:
        return investigation["error"]

    pod = investigation["pod"]
    deployment = investigation["deployment"]
    events = investigation["events"]
    logs = investigation["logs"]

    # ---------------------------------------------------------
    # Determine current runtime health
    # ---------------------------------------------------------

    status = pod["phase"]

    restarts = sum(
        container["restart_count"]
        for container in pod["containers"]
    )

    containers_ready = all(
        container["ready"]
        for container in pod["containers"]
    )

    healthy = (
        status == "Running"
        and containers_ready
        and restarts == 0
    )

    # ---------------------------------------------------------
    # Collect policy/configuration findings
    # ---------------------------------------------------------

    policy_findings = set()

    for event in events:
        reason = event.get("reason")
        message = event.get("message", "").lower()

        if reason != "PolicyViolation":
            continue

        if "unknown registr" in message:
            policy_findings.add(
                "Images from unknown registries are blocked by policy"
            )

        if "mutable image tag" in message or "latest" in message:
            policy_findings.add(
                "Image is using a mutable tag: latest"
            )

    # ---------------------------------------------------------
    # Build report
    # ---------------------------------------------------------

    lines = []

    lines.append("Pod Investigation")
    lines.append("────────────────────────────")
    lines.append(f"Pod: {pod['name']}")

    if healthy:
        lines.append("Current Health: HEALTHY")
    else:
        lines.append("Current Health: UNHEALTHY")

    lines.append("")

    # Runtime health
    lines.append("Current Runtime Health:")

    if status == "Running":
        lines.append("✓ Pod is Running")
    else:
        lines.append(f"⚠ Pod status: {status}")

    if containers_ready:
        lines.append("✓ All containers are Ready")
    else:
        lines.append("⚠ One or more containers are not Ready")

    # Inspect container states
    container_failures = []

    for container in pod["containers"]:
        if not container["ready"]:
            container_failures.append(
                f"{container['name']}: not ready"
            )

    # Get detailed container state from Kubernetes events
    event_messages = [
        event.get("message", "")
        for event in events
    ]

    image_pull_failure = any(
        "failed to pull image" in message.lower()
        or "imagepullbackoff" in message.lower()
        or "errimagepull" in message.lower()
        for message in event_messages
    )

    if image_pull_failure:
        lines.append("⚠ Container image could not be pulled")

    if restarts == 0:
        lines.append("✓ No container restarts detected")
    else:
        lines.append(f"⚠ Container restarts: {restarts}")

    if "200" in logs:
        lines.append("✓ Logs contain successful HTTP 200 responses")
    elif "Logs unavailable" in logs:
        lines.append("⚠ Container logs are unavailable because the container has not started")
  
  # Deployment
    if deployment:
        lines.append("")
        lines.append("Deployment:")
        lines.append(f"Name: {deployment['name']}")

        replicas = deployment["replicas"]
        available = deployment["available_replicas"]

        lines.append(f"Replicas: {available}/{replicas}")

    # Policy/configuration findings
    lines.append("")
    lines.append("Configuration / Policy Findings:")

    if policy_findings:
        for finding in sorted(policy_findings):
            lines.append(f"⚠ {finding}")
    else:
        lines.append("✓ No policy violations detected")

    # Assessment
    lines.append("")
    lines.append("Assessment:")

    if healthy and policy_findings:
        lines.append(
            "The pod is currently healthy from a runtime perspective. "
            "However, its configuration has policy violations that "
            "should be corrected."
        )

    elif healthy:
        lines.append(
            "The pod is currently healthy with no obvious runtime "
            "or policy problems detected."
        )

    elif image_pull_failure:
        lines.append(
            "The pod is unhealthy because the container image "
            "could not be pulled. Kubernetes reports an image "
            "pull failure."
        )

    else:
        lines.append(
            "The pod is currently unhealthy and requires further "
            "investigation."
        )
    return "\n".join(lines)

def investigate_unhealthy_pods(
    namespace: str = "default",
):
    """
    Discover unhealthy pods and investigate each one.

    Workflow:
        Find unhealthy pods
        -> Investigate each pod
        -> Generate human-readable explanation

    This function is read-only.
    """

    unhealthy_pods = find_pods(
        namespace=namespace,
        health="unhealthy",
    )

    results = []

    for pod in unhealthy_pods:
        investigation = investigate_pod(
            pod_name=pod["name"],
            namespace=namespace,
        )

        summary = summarize_investigation(
            investigation
        )

        results.append({
            "pod": pod["name"],
            "investigation": investigation,
            "summary": summary,
        })

    return results

from agent.llm import ask_llm

from rag import search_knowledge

def analyze_with_llm(investigation):
    """
    Use GitHub Copilot to analyze Kubernetes investigation evidence.

    The LLM is read-only and receives evidence collected by our
    Kubernetes investigation tools. It does not interact with Kubernetes.
    """

    retrieval_query_parts = [
        "Kubernetes",
        str(investigation["pod"].get("phase", "")),
    ]

    for container in investigation["pod"].get("containers", []):
        retrieval_query_parts.extend(
            [
                container.get("state", ""),
                container.get("reason", ""),
            ]
        )

    for event in investigation.get("events", []):
        retrieval_query_parts.append(
            event.get("reason", "")
    )

    retrieval_query = " ".join(retrieval_query_parts)
    
    print(f"[AGENT] RAG query: {retrieval_query}")

    knowledge = search_knowledge(retrieval_query)

    print("\n[AGENT] Retrieved knowledge:")

    if knowledge:
        print(f"[AGENT] Retrieved {len(knowledge)} document(s).")

        for item in knowledge:
            print(
                f"  - {item['file']} "
                f"(score: {item['score']})"
            )
    else:
        print("[AGENT] No relevant knowledge found.")

    prompt = f"""
You are a Kubernetes troubleshooting assistant.

Analyze the following Kubernetes investigation evidence.

Your task:
1. Identify the most likely root cause.
2. Explain the evidence supporting the conclusion.
3. Distinguish confirmed facts from assumptions.
4. Recommend safe next steps.
5. Do not suggest modifying production resources.
6. Do not invent information that is not present in the evidence.

Investigation evidence:

{investigation}

Retrieved knowledge from the DevOps knowledge base:

{chr(10).join(
    f"Document: {item['file']} (relevance score: {item['score']})\n{item['content']}"
    for item in knowledge
)}
"""
    return ask_llm(prompt)
