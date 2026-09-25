import subprocess

import yaml


def run_helm_command(command: list[str]):
    """
    Run a read-only Helm command and return its output.
    """

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

    except subprocess.CalledProcessError as exc:
        return {
            "success": False,
            "error": exc.stderr.strip(),
        }

    return {
        "success": True,
        "output": result.stdout,
    }


def get_helm_values(
    release_name: str,
    namespace: str,
):
    """
    Collect user-supplied Helm values for a release.

    This function is read-only and does not modify
    the Helm release or Kubernetes resources.
    """

    command = [
        "helm",
        "get",
        "values",
        release_name,
        "--namespace",
        namespace,
        "--output",
        "yaml",
    ]

    result = run_helm_command(command)

    if not result["success"]:
        return {
            "release": release_name,
            "namespace": namespace,
            **result,
        }

    try:
        values = yaml.safe_load(result["output"]) or {}

    except yaml.YAMLError as exc:
        return {
            "release": release_name,
            "namespace": namespace,
            "success": False,
            "error": f"Unable to parse Helm values: {exc}",
        }

    return {
        "release": release_name,
        "namespace": namespace,
        "success": True,
        "values": values,
    }


def get_helm_status(
    release_name: str,
    namespace: str,
):
    """
    Collect Helm release status.

    This function is read-only and does not modify
    the Helm release or Kubernetes resources.
    """

    command = [
        "helm",
        "status",
        release_name,
        "--namespace",
        namespace,
    ]

    result = run_helm_command(command)

    if not result["success"]:
        return {
            "release": release_name,
            "namespace": namespace,
            **result,
        }

    return {
        "release": release_name,
        "namespace": namespace,
        "success": True,
        "status": result["output"],
    }

from kubernetes import client, config


def find_helm_release_for_resource(
    resource_type: str,
    resource_name: str,
    namespace: str,
):
    """
    Discover the Helm release associated with a Kubernetes resource.

    This function is read-only and uses Kubernetes metadata to
    determine whether the resource is Helm-managed.
    """

    config.load_kube_config()

    api = client.AppsV1Api()

    if resource_type.lower() == "deployment":
        resource = api.read_namespaced_deployment(
            name=resource_name,
            namespace=namespace,
        )
    else:
        return {
            "success": False,
            "error": (
                f"Unsupported resource type: {resource_type}"
            ),
        }

    labels = resource.metadata.labels or {}
    annotations = resource.metadata.annotations or {}

    release_name = annotations.get(
        "meta.helm.sh/release-name"
    )

    release_namespace = annotations.get(
        "meta.helm.sh/release-namespace"
    )

    flux_release_name = labels.get(
        "helm.toolkit.fluxcd.io/name"
    )

    flux_release_namespace = labels.get(
        "helm.toolkit.fluxcd.io/namespace"
    )

    return {
        "success": True,
        "resource": {
            "type": resource_type,
            "name": resource_name,
            "namespace": namespace,
        },
        "helm": {
            "managed": bool(
                release_name
                or flux_release_name
                or labels.get(
                    "app.kubernetes.io/managed-by"
                ) == "Helm"
            ),
            "release_name": release_name,
            "release_namespace": release_namespace,
        },
        "flux": {
            "managed": bool(
                flux_release_name
                or flux_release_namespace
            ),
            "release_name": flux_release_name,
            "release_namespace": flux_release_namespace,
        },
    }

def parse_helm_metadata(output: str):
    """
    Parse Helm metadata output into structured evidence.
    """

    fields = {}

    for line in output.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)

        fields[key.strip().lower()] = value.strip()

    return {
        "name": fields.get("name"),
        "chart": fields.get("chart"),
        "version": fields.get("version"),
        "app_version": fields.get("app_version"),
        "namespace": fields.get("namespace"),
        "revision": fields.get("revision"),
        "status": fields.get("status"),
        "deployed_at": fields.get("deployed_at"),
        "apply_method": fields.get("apply_method"),
    }

def investigate_helm_release(
    release_name: str,
    namespace: str,
):
    """
    Collect read-only evidence for a Helm release.
    """

    metadata_result = run_helm_command(
        [
            "helm",
            "get",
            "metadata",
            release_name,
            "--namespace",
            namespace,
        ]
    )

    manifest_result = run_helm_command(
        [
            "helm",
            "get",
            "manifest",
            release_name,
            "--namespace",
            namespace,
        ]
    )

    values_result = get_helm_values(
        release_name,
        namespace,
    )

    status_result = get_helm_status(
        release_name,
        namespace,
    )

    if metadata_result["success"]:
        metadata = parse_helm_metadata(
            metadata_result["output"]
        )

    return {
        "release": release_name,
        "namespace": namespace,
        "metadata": metadata,
        "metadata_raw": metadata_result,
        "values": values_result,
        "status": status_result,
        "manifest": manifest_result,
    }

