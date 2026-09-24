from dataclasses import dataclass
import re


@dataclass
class DevOpsRequest:
    """
    Structured representation of a user's DevOps request.
    """

    intent: str
    resource_type: str | None = None
    resource_name: str | None = None
    namespace: str | None = None
    original_request: str = ""


def understand_request(request: str) -> DevOpsRequest:
    """
    Convert a natural-language DevOps request into a structured request.
    """

    request_lower = request.lower()

    resource_type = None
    resource_name = None
    intent = "unknown"

    # Detect pod-related requests.
    if "pod" in request_lower:
        resource_type = "pod"

    # Detect investigation intent.
    investigation_words = [
        "why",
        "investigate",
        "check",
        "troubleshoot",
        "problem",
        "issue",
        "failing",
        "failed",
        "not running",
        "not ready",
        "unhealthy",
        "error",
    ]

    if any(word in request_lower for word in investigation_words):
        intent = "investigate"

    # Try to identify a Kubernetes pod name.
    pod_name_pattern = r"\b[a-z0-9][a-z0-9.-]*-[a-z0-9]+\b"

    matches = re.findall(
        pod_name_pattern,
        request_lower,
    )

    if matches:
        resource_name = matches[0]

        # If the request contains a Kubernetes-style resource name
        # but does not explicitly mention the resource type, assume
        # pod for the current pod-investigation capability.
        if resource_type is None:
            resource_type = "pod"

    return DevOpsRequest(
        intent=intent,
        resource_type=resource_type,
        resource_name=resource_name,
        original_request=request,
    )
