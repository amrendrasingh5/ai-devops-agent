# Kubernetes Troubleshooting Guide

## ImagePullBackOff

### Symptoms

A pod may show:

- STATUS: ImagePullBackOff
- STATUS: ErrImagePull
- Container state: Waiting
- Container reason: ImagePullBackOff
- Events containing Failed to pull image
- Events containing Back-off pulling image

### Common Causes

1. The container image does not exist.
2. The image tag is incorrect.
3. The container registry is unavailable.
4. The cluster cannot reach the registry.
5. The image is private and requires authentication.
6. A Kubernetes admission policy blocks the image registry.
7. The image architecture is incompatible with the node architecture.

### Investigation

Check the pod:

    kubectl describe pod <pod-name> -n <namespace>

Check events:

    kubectl get events -n <namespace> --sort-by=.lastTimestamp

Check the image configured on the pod:

    kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'

Check whether the pod is managed by a controller such as a Deployment, ReplicaSet, StatefulSet, or DaemonSet.

### Diagnosis

If the event says the image or manifest was not found, verify the image name and tag in the source manifest, Helm chart, or Git repository.

If the event indicates authentication failure, verify that the required image pull secret or workload identity configuration exists.

If an admission policy reports a registry violation, inspect the applicable Kyverno or other admission policy and verify whether the registry is allowed.

### Safe Remediation

Do not patch production resources directly.

For workloads managed through GitOps or infrastructure-as-code:

1. Identify the source manifest, Helm chart, or Terraform configuration.
2. Correct the image reference in source control.
3. Validate the change.
4. Create a pull request.
5. Allow the normal deployment/GitOps process to apply the change.

For a standalone test pod, confirm that the pod is intentionally created for testing before deleting or recreating it.

### Important Evidence

A pod in ImagePullBackOff normally has not successfully started its container.

Therefore:

- Container logs may be unavailable.
- restartCount may remain 0.
- Kubernetes events are often the primary source of evidence.
- A successful Scheduled event indicates that scheduling occurred; it does not prove that the container image can be pulled.

Always distinguish confirmed Kubernetes evidence from assumptions.
