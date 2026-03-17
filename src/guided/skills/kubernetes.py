import json
from typing import Optional

import yaml
from kubernetes import client, config, dynamic
from kubernetes.stream import stream as k8s_stream

# Maps resource type strings (as used in kubectl) to (api_version, kind) tuples
RESOURCE_KINDS: dict[str, tuple[str, str]] = {
    # Core (v1)
    "pod": ("v1", "Pod"),
    "pods": ("v1", "Pod"),
    "po": ("v1", "Pod"),
    "service": ("v1", "Service"),
    "services": ("v1", "Service"),
    "svc": ("v1", "Service"),
    "namespace": ("v1", "Namespace"),
    "namespaces": ("v1", "Namespace"),
    "ns": ("v1", "Namespace"),
    "node": ("v1", "Node"),
    "nodes": ("v1", "Node"),
    "no": ("v1", "Node"),
    "configmap": ("v1", "ConfigMap"),
    "configmaps": ("v1", "ConfigMap"),
    "cm": ("v1", "ConfigMap"),
    "secret": ("v1", "Secret"),
    "secrets": ("v1", "Secret"),
    "persistentvolumeclaim": ("v1", "PersistentVolumeClaim"),
    "persistentvolumeclaims": ("v1", "PersistentVolumeClaim"),
    "pvc": ("v1", "PersistentVolumeClaim"),
    "event": ("v1", "Event"),
    "events": ("v1", "Event"),
    "ev": ("v1", "Event"),
    # Apps (apps/v1)
    "deployment": ("apps/v1", "Deployment"),
    "deployments": ("apps/v1", "Deployment"),
    "deploy": ("apps/v1", "Deployment"),
    "statefulset": ("apps/v1", "StatefulSet"),
    "statefulsets": ("apps/v1", "StatefulSet"),
    "sts": ("apps/v1", "StatefulSet"),
    "daemonset": ("apps/v1", "DaemonSet"),
    "daemonsets": ("apps/v1", "DaemonSet"),
    "ds": ("apps/v1", "DaemonSet"),
    "replicaset": ("apps/v1", "ReplicaSet"),
    "replicasets": ("apps/v1", "ReplicaSet"),
    "rs": ("apps/v1", "ReplicaSet"),
    # Batch
    "job": ("batch/v1", "Job"),
    "jobs": ("batch/v1", "Job"),
    "cronjob": ("batch/v1", "CronJob"),
    "cronjobs": ("batch/v1", "CronJob"),
    "cj": ("batch/v1", "CronJob"),
    # Networking
    "ingress": ("networking.k8s.io/v1", "Ingress"),
    "ingresses": ("networking.k8s.io/v1", "Ingress"),
    "ing": ("networking.k8s.io/v1", "Ingress"),
}

CLUSTER_SCOPED = {"Namespace", "Node", "PersistentVolume"}


def _load_config() -> None:
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()


def _dynamic_client() -> dynamic.DynamicClient:
    _load_config()
    return dynamic.DynamicClient(client.ApiClient())


def _resolve_resource(resource_type: str) -> dynamic.Resource:
    key = resource_type.lower()
    if key not in RESOURCE_KINDS:
        known = sorted({v[1] for v in RESOURCE_KINDS.values()})
        raise ValueError(
            f"Unknown resource type '{resource_type}'. Known types: {', '.join(known)}"
        )
    api_version, kind = RESOURCE_KINDS[key]
    return _dynamic_client().resources.get(api_version=api_version, kind=kind)


def _format(obj: object, output: Optional[str]) -> str:
    data = obj.to_dict()
    if output == "json":
        return json.dumps(data, indent=2, default=str)
    if output == "name":
        items = data.get("items")
        if items is not None:
            return "\n".join(
                f"{i.get('kind', '').lower()}/{i['metadata']['name']}" for i in items
            )
        return f"{data.get('kind', '').lower()}/{data['metadata']['name']}"
    return yaml.dump(data, default_flow_style=False)


def kubectl_get(
    resource: str,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    output: Optional[str] = None,
    all_namespaces: bool = False,
    label_selector: Optional[str] = None,
) -> str:
    """
    List or get Kubernetes resources (pods, services, deployments, configmaps, etc.).

    Args:
        resource: Resource type to get (e.g. pods, services, deployments, nodes, configmaps).
        name: Optional name of a specific resource to get.
        namespace: Namespace to query. Defaults to the current namespace context.
        output: Output format: json, yaml, or name.
        all_namespaces: If True, list resources across all namespaces.
        label_selector: Filter resources by label selector (e.g. 'app=my-app').

    Returns:
        The resource data in the requested format.
    """
    try:
        res = _resolve_resource(resource)
        kwargs: dict = {}
        if label_selector:
            kwargs["label_selector"] = label_selector
        if not all_namespaces and namespace:
            kwargs["namespace"] = namespace
        if name:
            kwargs["name"] = name
        obj = res.get(**kwargs)
        return _format(obj, output)
    except Exception as e:
        return f"Error: {e}"


def kubectl_describe(
    resource: str,
    name: str,
    namespace: Optional[str] = None,
) -> str:
    """
    Show detailed information about a specific Kubernetes resource.

    Args:
        resource: Resource type (e.g. pod, service, deployment, node).
        name: Name of the resource to describe.
        namespace: Namespace of the resource. Defaults to the current namespace context.

    Returns:
        YAML representation of the resource with full detail.
    """
    try:
        res = _resolve_resource(resource)
        kwargs: dict = {"name": name}
        if namespace:
            kwargs["namespace"] = namespace
        obj = res.get(**kwargs)
        return yaml.dump(obj.to_dict(), default_flow_style=False)
    except Exception as e:
        return f"Error: {e}"


def kubectl_logs(
    pod_name: str,
    namespace: Optional[str] = None,
    container: Optional[str] = None,
    tail: Optional[int] = None,
    previous: bool = False,
    label_selector: Optional[str] = None,
) -> str:
    """
    Fetch logs from a pod or a set of pods matched by label selector.

    Args:
        pod_name: Name of the pod to retrieve logs from. Ignored if label_selector is provided.
        namespace: Namespace of the pod. Defaults to 'default'.
        container: Name of a specific container within the pod.
        tail: Number of most recent log lines to show.
        previous: If True, return logs from the previous (terminated) container instance.
        label_selector: Select pods by label (e.g. 'app=my-app') instead of by name.

    Returns:
        Log output from the pod(s).
    """
    try:
        _load_config()
        v1 = client.CoreV1Api()
        ns = namespace or "default"
        kwargs: dict = {}
        if container:
            kwargs["container"] = container
        if tail is not None:
            kwargs["tail_lines"] = tail
        if previous:
            kwargs["previous"] = True

        if label_selector:
            pods = v1.list_namespaced_pod(namespace=ns, label_selector=label_selector)
            logs = []
            for pod in pods.items:
                log = v1.read_namespaced_pod_log(
                    name=pod.metadata.name, namespace=ns, **kwargs
                )
                logs.append(f"==> {pod.metadata.name} <==\n{log}")
            return "\n".join(logs) if logs else "No pods matched the label selector."

        return v1.read_namespaced_pod_log(name=pod_name, namespace=ns, **kwargs)
    except Exception as e:
        return f"Error: {e}"


def kubectl_exec(
    pod_name: str,
    command: str,
    namespace: Optional[str] = None,
    container: Optional[str] = None,
) -> str:
    """
    Execute a command inside a running pod.

    Args:
        pod_name: Name of the pod to execute the command in.
        command: Shell command to run inside the pod (passed via sh -c).
        namespace: Namespace of the pod. Defaults to 'default'.
        container: Name of a specific container within the pod.

    Returns:
        Output of the executed command.
    """
    try:
        _load_config()
        v1 = client.CoreV1Api()
        ns = namespace or "default"
        kwargs: dict = {
            "command": ["/bin/sh", "-c", command],
            "stderr": True,
            "stdin": False,
            "stdout": True,
            "tty": False,
        }
        if container:
            kwargs["container"] = container
        return k8s_stream(v1.connect_get_namespaced_pod_exec, pod_name, ns, **kwargs)
    except Exception as e:
        return f"Error: {e}"


def kubectl_apply(
    manifest: str,
    namespace: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """
    Apply a Kubernetes manifest (YAML or JSON) to the cluster using server-side apply.

    Args:
        manifest: YAML or JSON manifest content to apply.
        namespace: Namespace to apply the manifest into. Defaults to namespace in manifest or current context.
        dry_run: If True, perform a server-side dry run without making changes.

    Returns:
        A summary of created or updated resources.
    """
    try:
        dyn = _dynamic_client()
        results = []
        for doc in yaml.safe_load_all(manifest):
            if not doc:
                continue
            api_version = doc.get("apiVersion", "v1")
            kind = doc.get("kind", "")
            res = dyn.resources.get(api_version=api_version, kind=kind)
            ns = namespace or doc.get("metadata", {}).get("namespace")
            kwargs: dict = {"field_manager": "guided"}
            if dry_run:
                kwargs["dry_run"] = "All"
            if ns and kind not in CLUSTER_SCOPED:
                kwargs["namespace"] = ns
            obj = dyn.server_side_apply(res, doc, **kwargs)
            name = obj.metadata.name
            results.append(f"{kind.lower()}/{name} applied")
        return "\n".join(results) if results else "No resources found in manifest."
    except Exception as e:
        return f"Error: {e}"


def kubectl_delete(
    resource: str,
    name: str,
    namespace: Optional[str] = None,
) -> str:
    """
    Delete a Kubernetes resource by type and name.

    Args:
        resource: Resource type to delete (e.g. pod, service, deployment).
        name: Name of the resource to delete.
        namespace: Namespace of the resource. Defaults to the current namespace context.

    Returns:
        Confirmation of deletion or an error message.
    """
    try:
        res = _resolve_resource(resource)
        kwargs: dict = {"name": name}
        if namespace:
            kwargs["namespace"] = namespace
        res.delete(**kwargs)
        return f"{resource}/{name} deleted"
    except Exception as e:
        return f"Error: {e}"


def kubectl_rollout_status(
    resource: str,
    name: str,
    namespace: Optional[str] = None,
) -> str:
    """
    Check the rollout status of a Kubernetes deployment, daemonset, or statefulset.

    Args:
        resource: Resource type (deployment, daemonset, or statefulset).
        name: Name of the resource.
        namespace: Namespace of the resource. Defaults to 'default'.

    Returns:
        A human-readable rollout status summary.
    """
    try:
        _load_config()
        apps = client.AppsV1Api()
        ns = namespace or "default"
        key = resource.lower()

        if key in ("deployment", "deployments", "deploy"):
            obj = apps.read_namespaced_deployment(name=name, namespace=ns)
            spec_replicas = obj.spec.replicas or 0
            status = obj.status
            ready = status.ready_replicas or 0
            updated = status.updated_replicas or 0
            available = status.available_replicas or 0
            if (
                updated == spec_replicas
                and available == spec_replicas
                and ready == spec_replicas
            ):
                return f"deployment/{name} successfully rolled out ({ready}/{spec_replicas} replicas ready)"
            return (
                f"deployment/{name} rollout in progress: "
                f"{updated}/{spec_replicas} updated, "
                f"{available}/{spec_replicas} available, "
                f"{ready}/{spec_replicas} ready"
            )

        if key in ("statefulset", "statefulsets", "sts"):
            obj = apps.read_namespaced_stateful_set(name=name, namespace=ns)
            spec_replicas = obj.spec.replicas or 0
            ready = obj.status.ready_replicas or 0
            return (
                f"statefulset/{name}: {ready}/{spec_replicas} replicas ready"
                if ready == spec_replicas
                else f"statefulset/{name} rollout in progress: {ready}/{spec_replicas} ready"
            )

        if key in ("daemonset", "daemonsets", "ds"):
            obj = apps.read_namespaced_daemon_set(name=name, namespace=ns)
            desired = obj.status.desired_number_scheduled or 0
            ready = obj.status.number_ready or 0
            return (
                f"daemonset/{name}: {ready}/{desired} nodes ready"
                if ready == desired
                else f"daemonset/{name} rollout in progress: {ready}/{desired} nodes ready"
            )

        return f"Error: rollout status is not supported for resource type '{resource}'"
    except Exception as e:
        return f"Error: {e}"
