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
    tail_lines: int = 100,
    previous: bool = False,
):
    """
    Return recent logs from a Kubernetes pod.

    This function is read-only.

    If previous=True, return logs from the previous
    terminated container instance.

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
            previous=previous,
        )

        if isinstance(logs, bytes):
            return logs.decode("utf-8", errors="replace")

        if isinstance(logs, str) and logs.startswith("b'") and logs.endswith("'"):
            return logs[2:-1].encode("utf-8").decode("unicode_escape")

        return logs

    except client.exceptions.ApiException as e:
        if e.status == 400 and "waiting to start" in str(e.body):
            return "Logs unavailable: container has not started."

        if previous and e.status in {400, 404}:
            return "Previous logs unavailable: no previous container instance exists."

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

def get_services(namespace: str = "default"):
    """
    Return Kubernetes Services in a namespace.

    This function is read-only.
    """
    config.load_kube_config()

    v1 = client.CoreV1Api()

    services = v1.list_namespaced_service(
        namespace=namespace,
    )

    result = []

    for service in services.items:
        result.append({
            "name": service.metadata.name,
            "namespace": service.metadata.namespace,
            "type": service.spec.type,
            "cluster_ip": service.spec.cluster_ip,
            "ports": [
                {
                    "name": port.name,
                    "port": port.port,
                    "target_port": str(port.target_port),
                    "protocol": port.protocol,
                }
                for port in (service.spec.ports or [])
            ],
            "selector": service.spec.selector or {},
        })

    return result

def get_endpoint_slices(namespace: str = "default"):
    """
    Return Kubernetes EndpointSlices in a namespace.

    This function is read-only.
    """
    config.load_kube_config()

    discovery_v1 = client.DiscoveryV1Api()

    endpoint_slices = discovery_v1.list_namespaced_endpoint_slice(
        namespace=namespace,
    )

    result = []

    for endpoint_slice in endpoint_slices.items:
        endpoints = []

        for endpoint in endpoint_slice.endpoints:
            addresses = endpoint.addresses or []

            conditions = endpoint.conditions

            endpoints.append({
                "addresses": addresses,
                "ready": conditions.ready,
                "serving": conditions.serving,
                "terminating": conditions.terminating,
                "node_name": endpoint.node_name,
                "target_ref": (
                    {
                        "kind": endpoint.target_ref.kind,
                        "name": endpoint.target_ref.name,
                    }
                    if endpoint.target_ref
                    else None
                ),
            })

        result.append({
            "name": endpoint_slice.metadata.name,
            "namespace": endpoint_slice.metadata.namespace,
            "service_name": (
                endpoint_slice.metadata.labels or {}
            ).get("kubernetes.io/service-name"),
            "address_type": endpoint_slice.address_type,
            "ports": [
                {
                    "name": port.name,
                    "port": port.port,
                    "protocol": port.protocol,
                }
                for port in (endpoint_slice.ports or [])
            ],
            "endpoints": endpoints,
        })

    return result

def get_service_network_evidence(namespace: str = "default"):
    """
    Collect Service and EndpointSlice evidence for a namespace.

    This function is read-only.
    """
    services = get_services(namespace)
    endpoint_slices = get_endpoint_slices(namespace)

    return {
        "services": services,
        "endpoint_slices": endpoint_slices,
    }

def get_ingresses(namespace: str = "default"):
    """
    Return Kubernetes Ingress resources in a namespace.

    This function is read-only.
    """
    config.load_kube_config()

    networking_v1 = client.NetworkingV1Api()

    ingresses = networking_v1.list_namespaced_ingress(
        namespace=namespace,
    )

    result = []

    for ingress in ingresses.items:
        rules = []

        for rule in (ingress.spec.rules or []):
            paths = []

            if rule.http:
                for path in (rule.http.paths or []):
                    backend = path.backend

                    service = None

                    if backend.service:
                        service = {
                            "name": backend.service.name,
                            "port": (
                                backend.service.port.number
                                if backend.service.port.number is not None
                                else backend.service.port.name
                            ),
                        }

                    paths.append({
                        "path": path.path,
                        "path_type": path.path_type,
                        "service": service,
                    })

            rules.append({
                "host": rule.host,
                "paths": paths,
            })

        result.append({
            "name": ingress.metadata.name,
            "namespace": ingress.metadata.namespace,
            "ingress_class": (
                ingress.spec.ingress_class_name
            ),
            "rules": rules,
            "load_balancer": [
                {
                    "hostname": status.hostname,
                    "ip": status.ip,
                }
                for status in (
                    ingress.status.load_balancer.ingress or []
                )
            ],
        })

    return result

def get_all_ingresses():
    """
    Return Kubernetes Ingress resources across all namespaces.

    This function is read-only.
    """
    config.load_kube_config()

    networking_v1 = client.NetworkingV1Api()

    ingresses = networking_v1.list_ingress_for_all_namespaces()

    result = []

    for ingress in ingresses.items:
        rules = []

        for rule in (ingress.spec.rules or []):
            paths = []

            if rule.http:
                for path in (rule.http.paths or []):
                    backend = path.backend

                    service = None

                    if backend.service:
                        service = {
                            "name": backend.service.name,
                            "port": (
                                backend.service.port.number
                                if backend.service.port.number is not None
                                else backend.service.port.name
                            ),
                        }

                    paths.append({
                        "path": path.path,
                        "path_type": path.path_type,
                        "service": service,
                    })

            rules.append({
                "host": rule.host,
                "paths": paths,
            })

        result.append({
            "name": ingress.metadata.name,
            "namespace": ingress.metadata.namespace,
            "ingress_class": ingress.spec.ingress_class_name,
            "rules": rules,
            "load_balancer": [
                {
                    "hostname": status.hostname,
                    "ip": status.ip,
                }
                for status in (
                    ingress.status.load_balancer.ingress or []
                )
            ],
        })

    return result

def find_ingresses_by_hostname(hostname: str):
    """
    Find Kubernetes Ingress resources matching a hostname.

    This function is read-only.
    """
    ingresses = get_all_ingresses()

    matches = []

    for ingress in ingresses:
        for rule in ingress.get("rules", []):
            rule_host = rule.get("host")

            if rule_host == hostname:
                matches.append({
                    "ingress": ingress,
                    "matched_host": rule_host,
                })

    return matches

def find_service_endpoints(
    service_name: str,
    namespace: str,
):
    """
    Find EndpointSlice evidence for a Kubernetes Service.

    This function is read-only.
    """
    endpoint_slices = get_endpoint_slices(namespace)

    matches = []

    for endpoint_slice in endpoint_slices:
        if endpoint_slice.get("service_name") == service_name:
            matches.append(endpoint_slice)

    return matches
def get_endpoint_pod_evidence(
    endpoint_slices: list,
    namespace: str,
):
    """
    Collect Kubernetes Pod evidence for EndpointSlice targets.

    This function is read-only.
    """
    pod_names = []

    for endpoint_slice in endpoint_slices:
        for endpoint in endpoint_slice.get("endpoints", []):
            target_ref = endpoint.get("target_ref")

            if (
                target_ref
                and target_ref.get("kind") == "Pod"
                and target_ref.get("name")
            ):
                pod_names.append(target_ref["name"])

    pod_names = list(dict.fromkeys(pod_names))

    result = []

    for pod_name in pod_names:
        pods = get_pods(namespace)

        for pod in pods:
            if pod.get("name") == pod_name:
                result.append(pod)

    return result

def investigate_service_network_path(
    service_name: str,
    namespace: str,
):
    """
    Collect a read-only snapshot of the Service network path.

    Service -> EndpointSlice -> Pods
    """
    endpoint_slices = find_service_endpoints(
        service_name=service_name,
        namespace=namespace,
    )

    pods = get_endpoint_pod_evidence(
        endpoint_slices=endpoint_slices,
        namespace=namespace,
    )

    return {
        "service_name": service_name,
        "namespace": namespace,
        "endpoint_slices": endpoint_slices,
        "pods": pods,
    }

def investigate_url_kubernetes_path(
    hostname: str,
):
    """
    Collect read-only Kubernetes evidence for a URL hostname.

    Hostname -> Ingress -> Service -> EndpointSlice -> Pods
    """
    ingress_matches = find_ingresses_by_hostname(hostname)

    result = {
        "hostname": hostname,
        "ingresses": [],
    }

    for match in ingress_matches:
        ingress = match["ingress"]

        ingress_evidence = {
            "name": ingress["name"],
            "namespace": ingress["namespace"],
            "ingress_class": ingress["ingress_class"],
            "matched_host": match["matched_host"],
            "load_balancer": ingress["load_balancer"],
            "services": [],
        }

        for rule in ingress["rules"]:
            if rule["host"] != hostname:
                continue

            for path in rule["paths"]:
                service = path.get("service")

                if not service:
                    continue

                service_name = service["name"]
                namespace = ingress["namespace"]

                network = investigate_service_network_path(
                    service_name=service_name,
                    namespace=namespace,
                )

                ingress_evidence["services"].append({
                    "path": path["path"],
                    "path_type": path["path_type"],
                    "name": service_name,
                    "port": service["port"],
                    "network": network,
                })

        result["ingresses"].append(ingress_evidence)

    return result

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

def get_pod_details(
    pod_name: str,
    namespace: str = "default",
):
    """
    Return detailed Kubernetes configuration for a pod.

    This function is read-only.
    """

    config.load_kube_config()

    v1 = client.CoreV1Api()

    pod = v1.read_namespaced_pod(
        name=pod_name,
        namespace=namespace,
    )

    containers = []

    for container in pod.spec.containers:
        containers.append({
            "name": container.name,
            "image": container.image,
            "command": container.command,
            "args": container.args,
            "ports": [
                {
                    "name": port.name,
                    "container_port": port.container_port,
                    "protocol": port.protocol,
                }
                for port in (container.ports or [])
            ],
            "env": [
                {
                    "name": env.name,
                    "value": env.value,
                    "value_from": (
                        env.value_from.to_dict()
                        if env.value_from
                        else None
                    ),
                }
                for env in (container.env or [])
            ],
            "resources": (
                container.resources.to_dict()
                if container.resources
                else None
            ),
            "volume_mounts": [
                {
                    "name": mount.name,
                    "mount_path": mount.mount_path,
                    "read_only": mount.read_only,
                }
                for mount in (container.volume_mounts or [])
            ],
            "liveness_probe": (
                container.liveness_probe.to_dict()
                if container.liveness_probe
                else None
            ),
            "readiness_probe": (
                container.readiness_probe.to_dict()
                if container.readiness_probe
                else None
            ),
            "startup_probe": (
                container.startup_probe.to_dict()
                if container.startup_probe
                else None
            ),
        })

    volumes = []

    for volume in (pod.spec.volumes or []):
        volume_info = {
            "name": volume.name,
        }

        if volume.config_map:
            volume_info["type"] = "config_map"
            volume_info["config_map"] = {
                "name": volume.config_map.name,
                "optional": volume.config_map.optional,
            }

        elif volume.secret:
            volume_info["type"] = "secret"
            volume_info["secret"] = {
                "secret_name": volume.secret.secret_name,
                "optional": volume.secret.optional,
            }

        elif volume.persistent_volume_claim:
            volume_info["type"] = "persistent_volume_claim"
            volume_info["persistent_volume_claim"] = {
                "claim_name": volume.persistent_volume_claim.claim_name,
                "read_only": volume.persistent_volume_claim.read_only,
            }

        elif volume.empty_dir:
            volume_info["type"] = "empty_dir"

        elif volume.host_path:
            volume_info["type"] = "host_path"
            volume_info["host_path"] = {
                "path": volume.host_path.path,
                "type": volume.host_path.type,
            }

        elif volume.projected:
            volume_info["type"] = "projected"

        elif volume.csi:
            volume_info["type"] = "csi"
            volume_info["csi"] = {
                "driver": volume.csi.driver,
                "read_only": volume.csi.read_only,
            }

        else:
            volume_info["type"] = "other"

        volumes.append(volume_info)

    init_containers = []

    for container in (pod.spec.init_containers or []):
        init_containers.append({
            "name": container.name,
            "image": container.image,
            "command": container.command,
            "args": container.args,
        })

    return {
        "name": pod.metadata.name,
        "namespace": pod.metadata.namespace,
        "service_account": pod.spec.service_account_name,
        "node": pod.spec.node_name,
        "restart_policy": pod.spec.restart_policy,
        "containers": containers,
        "init_containers": init_containers,
        "volumes": volumes,
    }
