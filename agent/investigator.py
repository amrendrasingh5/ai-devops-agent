from agent.tools.kubernetes import (
    get_pods,
    get_pod_events,
    get_pod_logs,
    get_deployment,
    get_pod_deployment,
    get_pod_details,
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
    logs = {
        "current": get_pod_logs(
            pod_name,
            namespace,
        ),
        "previous": get_pod_logs(
            pod_name,
            namespace,
            previous=True,
    ),
}

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
    pod_details = get_pod_details(
        pod_name,
        namespace,
)
    return {
        "pod": pod,
        "events": events,
        "logs": logs,
        "deployment": deployment,
        "pod_details": pod_details,
    }

def summarize_investigation(investigation):
    """
    Convert investigation evidence into a human-readable evidence summary.

    This function reports collected evidence only.
    Root-cause analysis is performed by the LLM.
    This function does not modify Kubernetes resources.
    """

    if "error" in investigation:
        return investigation["error"]

    pod = investigation["pod"]
    deployment = investigation.get("deployment")
    events = investigation.get("events", [])
    logs = investigation.get("logs", {})
    pod_details = investigation.get("pod_details")

    status = pod.get("phase")

    containers = pod.get("containers", [])

    containers_ready = (
        bool(containers)
        and all(
            container.get("ready", False)
            for container in containers
        )
    )

    lines = []

    lines.append("Pod Investigation Evidence")
    lines.append("────────────────────────────")
    lines.append(f"Pod: {pod.get('name')}")
    lines.append(f"Namespace: {pod.get('namespace')}")
    lines.append(f"Pod phase: {status}")
    lines.append("")

    # Container evidence
    lines.append("Container Evidence:")

    if containers:
        for container in containers:
            lines.append(
                f"- Name: {container.get('name')}"
            )
            lines.append(
                f"  Ready: {container.get('ready')}"
            )
            lines.append(
                f"  State: {container.get('state')}"
            )
            lines.append(
                f"  Reason: {container.get('reason')}"
            )
            lines.append(
                f"  Restart count: "
                f"{container.get('restart_count')}"
            )
            lines.append(
                f"  Image: {container.get('image')}"
            )
    else:
        lines.append("- No container status information available.")

    lines.append("")

    # Logs
    lines.append("Logs:")

    current_logs = logs.get("current", "")
    previous_logs = logs.get("previous", "")

    if current_logs.startswith("Logs unavailable"):
        lines.append(
            f"- Current logs: {current_logs}"
        )
    else:
        lines.append("- Current logs: available")

    if previous_logs.startswith("Previous logs unavailable"):
        lines.append(
            f"- Previous logs: {previous_logs}"
        )
    else:
        lines.append("- Previous logs: available")

    lines.append("")

    # Events
    lines.append("Events:")

    if events:
        for event in events:
            lines.append(
                f"- Type: {event.get('type')}"
            )
            lines.append(
                f"  Reason: {event.get('reason')}"
            )
            lines.append(
                f"  Message: {event.get('message')}"
            )
            lines.append(
                f"  Count: {event.get('count')}"
            )
    else:
        lines.append("- No events found.")

    lines.append("")

    # Pod configuration
    lines.append("Pod Configuration:")

    if pod_details:
        lines.append(
            f"- Node: {pod_details.get('node')}"
        )
        lines.append(
            f"- Service account: "
            f"{pod_details.get('service_account')}"
        )
        lines.append(
            f"- Restart policy: "
            f"{pod_details.get('restart_policy')}"
        )

        for container in pod_details.get("containers", []):
            lines.append(
                f"- Container '{container.get('name')}' "
                f"image: {container.get('image')}"
            )

            if container.get("ports"):
                lines.append(
                    f"  Ports: {container.get('ports')}"
                )

            if container.get("env"):
                lines.append(
                    f"  Environment variables: "
                    f"{container.get('env')}"
                )

            if container.get("resources"):
                lines.append(
                    f"  Resources: "
                    f"{container.get('resources')}"
                )

            if container.get("volume_mounts"):
                lines.append(
                    f"  Volume mounts: "
                    f"{container.get('volume_mounts')}"
                )

            if container.get("liveness_probe"):
                lines.append(
                    "  Liveness probe: configured"
                )

            if container.get("readiness_probe"):
                lines.append(
                    "  Readiness probe: configured"
                )

            if container.get("startup_probe"):
                lines.append(
                    "  Startup probe: configured"
                )

    else:
        lines.append("- Pod configuration details unavailable.")

    lines.append("")

    # Deployment
    lines.append("Deployment:")

    if deployment:
        lines.append(
            f"- Name: {deployment.get('name')}"
        )
        lines.append(
            f"- Replicas: {deployment.get('replicas')}"
        )
        lines.append(
            f"- Ready replicas: "
            f"{deployment.get('ready_replicas')}"
        )
        lines.append(
            f"- Available replicas: "
            f"{deployment.get('available_replicas')}"
        )
    else:
        lines.append("- No deployment information available.")

    lines.append("")

    # Neutral runtime status
    lines.append("Runtime Status:")

    if status == "Running" and containers_ready:
        lines.append(
            "- Pod phase is Running and all reported "
            "containers are Ready."
        )
    else:
        lines.append(
            "- Pod phase and/or container readiness indicate "
            "that the workload is not currently fully ready."
        )

    lines.append("")
    lines.append(
        "Note: This summary reports evidence only. "
        "Root-cause analysis should be performed using "
        "the collected evidence."
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
        container_state = container.get("state")
        container_reason = container.get("reason")

        if container_state:
            retrieval_query_parts.append(container_state)

        if container_reason:
            retrieval_query_parts.append(container_reason)

    event_reasons = {
        event.get("reason", "")
        for event in investigation.get("events", [])
        if event.get("reason")
    }

    retrieval_query_parts.extend(event_reasons)

    # Include application logs as additional evidence for RAG.
    # Logs are evidence only; they are not interpreted here.
    for log_name in ("current", "previous"):
        log_content = investigation.get("logs", {}).get(log_name, "")

        if log_content and not log_content.startswith(
            ("Logs unavailable", "Previous logs unavailable")
        ):
            retrieval_query_parts.append(log_content[:2000])

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
1. Determine the most likely root cause or causes from the available evidence.
2. Analyze all relevant evidence, including pod state, container state, logs, previous logs, events, deployment information, and any other evidence provided.
3. Read application logs carefully and use specific log messages as evidence when they are available.
4. Do not assume that a Kubernetes status such as Running or Ready means the application itself is healthy.
5. Distinguish clearly between confirmed facts, strong indications, and assumptions.
6. Explain the reasoning that connects the evidence to the suspected root cause.
7. Identify any important missing evidence that prevents a definitive conclusion.
8. Recommend practical and safe remediation steps based on the evidence.
9. Prefer changes through source control or GitOps rather than direct changes to live resources.
10. Do not modify Kubernetes resources.
11. Do not invent information that is not present in the evidence.
12. Do not assume the purpose or intent of a workload from its name, labels, or other naming conventions.
13. Do not invent or guess replacement image names, tags, versions, configuration values, or other remediation details.
14. If a specific replacement value is not present in the evidence or retrieved knowledge, state that the intended value must be determined from the source repository, Helm values, GitOps configuration, or other authoritative configuration.
15. When recommending remediation, describe what should be corrected without inventing an exact replacement value unless one is supported by the available evidence.

Investigation evidence:

{investigation}

Retrieved knowledge from the DevOps knowledge base:

{chr(10).join(
    f"Document: {item['file']} (relevance score: {item['score']})\n{item['content']}"
    for item in knowledge
)}
"""
    return ask_llm(prompt)
