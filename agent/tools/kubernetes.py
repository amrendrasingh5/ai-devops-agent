from kubernetes import client, config


def get_pods(namespace: str | None = None):
    """
    Return useful health information about pods.

    If namespace is provided, return pods from that namespace.
    If namespace is None, return pods from all namespaces.

    This function is read-only.
    """
    config.load_kube_config()

    v1 = client.CoreV1Api()

    if namespace:
        pods = v1.list_namespaced_pod(namespace=namespace)
    else:
        pods = v1.list_pod_for_all_namespaces()

    result = []

    for pod in pods.items:
        containers = []

        if pod.status.container_statuses:
            for container in pod.status.container_statuses:

                state = "unknown"
                reason = None
                message = None

                if container.state:
                    if container.state.running:
                        state = "running"

                    elif container.state.waiting:
                        state = "waiting"
                        reason = container.state.waiting.reason
                        message = container.state.waiting.message

                    elif container.state.terminated:
                        state = "terminated"
                        reason = container.state.terminated.reason
                        message = container.state.terminated.message

                containers.append({
                    "name": container.name,
                    "ready": container.ready,
                    "restart_count": container.restart_count,
                    "image": container.image,
                    "state": state,
                    "reason": reason,
                    "message": message,
                })

        result.append({
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "phase": pod.status.phase,
            "node": pod.spec.node_name,
            "containers": containers,
        })

    return result
def get_pod_events(
    pod_name: str,
    namespace: str = "default"
):
    """
    Return Kubernetes events related to a specific pod.

    This function is read-only.
    """
    config.load_kube_config()

    v1 = client.CoreV1Api()

    events = v1.list_namespaced_event(
        namespace=namespace,
        field_selector=f"involvedObject.name={pod_name}"
    )

    result = []

    for event in events.items:
        result.append({
            "type": event.type,
            "reason": event.reason,
            "message": event.message,
            "count": event.count,
            "first_timestamp": str(event.first_timestamp),
            "last_timestamp": str(event.last_timestamp),
        })

    return result

def get_pod_logs(
    pod_name: str,
    namespace: str = "default",
    container: str | None = None,
    tail_lines: int = 100
):
    """
    Return recent logs from a Kubernetes pod.

    This function is read-only.

    If the container has not started yet, logs may not be
    available. In that case, return a descriptive message
    instead of failing the investigation.
    """
    config.load_kube_config()

    v1 = client.CoreV1Api()

    try:
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines,
        )

        if isinstance(logs, bytes):
            return logs.decode("utf-8", errors="replace")

        if isinstance(logs, str) and logs.startswith("b'") and logs.endswith("'"):
            return logs[2:-1].encode("utf-8").decode("unicode_escape")

        return logs

    except client.exceptions.ApiException as e:
        if e.status == 400 and "waiting to start" in str(e.body):
            return "Logs unavailable: container has not started."

        return f"Logs unavailable: Kubernetes API returned HTTP {e.status}."
def get_deployment(
    deployment_name: str,
    namespace: str = "default"
):
    """
    Return useful information about a Kubernetes Deployment.

    This function is read-only.
    """
    config.load_kube_config()

    apps_v1 = client.AppsV1Api()

    deployment = apps_v1.read_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
    )

    containers = []

    for container in deployment.spec.template.spec.containers:
        containers.append({
            "name": container.name,
            "image": container.image,
            "ports": [
                port.container_port
                for port in (container.ports or [])
            ],
        })

    return {
        "name": deployment.metadata.name,
        "namespace": deployment.metadata.namespace,
        "replicas": deployment.spec.replicas,
        "available_replicas": deployment.status.available_replicas,
        "ready_replicas": deployment.status.ready_replicas,
        "updated_replicas": deployment.status.updated_replicas,
        "containers": containers,
    }

def get_deployment(
    deployment_name: str,
    namespace: str = "default"
):
    """
    Return useful information about a Kubernetes Deployment.

    This function is read-only.
    """
    config.load_kube_config()

    apps_v1 = client.AppsV1Api()

    deployment = apps_v1.read_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
    )

    containers = []

    for container in deployment.spec.template.spec.containers:
        containers.append({
            "name": container.name,
            "image": container.image,
            "ports": [
                port.container_port
                for port in (container.ports or [])
            ],
        })

    return {
        "name": deployment.metadata.name,
        "namespace": deployment.metadata.namespace,
        "replicas": deployment.spec.replicas,
        "available_replicas": deployment.status.available_replicas,
        "ready_replicas": deployment.status.ready_replicas,
        "updated_replicas": deployment.status.updated_replicas,
        "containers": containers,
    }


def get_pod_deployment(
    pod_name: str,
    namespace: str = "default",
):
    """
    Find the Deployment that owns a specific Pod.

    Ownership chain:
        Pod -> ReplicaSet -> Deployment

    This function is read-only.
    """
    config.load_kube_config()

    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    # Get the Pod
    pod = v1.read_namespaced_pod(
        name=pod_name,
        namespace=namespace,
    )

    # Find the ReplicaSet that owns the Pod
    replica_set_name = None

    if pod.metadata.owner_references:
        for owner in pod.metadata.owner_references:
            if owner.kind == "ReplicaSet":
                replica_set_name = owner.name
                break

    if replica_set_name is None:
        return None

    # Get the ReplicaSet
    replica_set = apps_v1.read_namespaced_replica_set(
        name=replica_set_name,
        namespace=namespace,
    )

    # Find the Deployment that owns the ReplicaSet
    if replica_set.metadata.owner_references:
        for owner in replica_set.metadata.owner_references:
            if owner.kind == "Deployment":
                return owner.name

    return None

def find_pods(
    namespace: str | None = None,
    health: str | None = None,
):
    """
    Find pods in Kubernetes.

    If namespace is provided, search only that namespace.
    If namespace is None, search all namespaces.

    Optional health filter:
        healthy
        unhealthy

    This function is read-only.
    """

    pods = get_pods(namespace)

    if health is None:
        return pods

    health = health.lower()

    if health not in {"healthy", "unhealthy"}:
        raise ValueError(
            "health must be 'healthy', 'unhealthy', or None"
        )

    result = []

    for pod in pods:
        containers = pod["containers"]

        is_healthy = (
            pod["phase"] == "Running"
            and all(container["ready"] for container in containers)
        )

        is_completed = pod["phase"] == "Succeeded"

        if health == "healthy" and is_healthy:
            result.append(pod)

        elif health == "unhealthy" and not is_healthy and not is_completed:
            result.append(pod)

    return result
