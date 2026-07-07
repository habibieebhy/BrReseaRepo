from typing import cast

from kubernetes import client, config
from kubernetes.client import (
    AppsV1Api,
    CoreV1Api,
    V1DeploymentList,
    V1PodList,
)
from kubernetes.config import ConfigException


def load_config() -> None:
    """
    Loads the Kubernetes configuration.

    Uses the local kubeconfig during development and the
    in-cluster configuration when running inside Kubernetes.
    """

    try:
        config.load_kube_config()
    except ConfigException:
        config.load_incluster_config()


def api() -> CoreV1Api:
    """
    Returns the Kubernetes Core API client.
    """

    load_config()
    return client.CoreV1Api()


def apps() -> AppsV1Api:
    """
    Returns the Kubernetes Apps API client.
    """

    load_config()
    return client.AppsV1Api()


def cluster_health() -> dict:
    """
    Returns Kubernetes cluster health.
    """

    try:
        api().get_api_resources()

        return {
            "provider": "kubernetes",
            "healthy": True,
        }

    except Exception as e:

        return {
            "provider": "kubernetes",
            "healthy": False,
            "error": str(e),
        }


def list_pods() -> dict:
    """
    Lists all Kubernetes pods.
    """

    pods = cast(
        V1PodList,
        api().list_pod_for_all_namespaces(),
    )

    return {
        "pods": [
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "node": pod.spec.node_name,
            }
            for pod in (pods.items or [])
        ]
    }


def list_deployments() -> dict:
    """
    Lists all Kubernetes deployments.
    """

    deployments = cast(
        V1DeploymentList,
        apps().list_deployment_for_all_namespaces(),
    )

    return {
        "deployments": [
            {
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.spec.replicas,
                "available": deployment.status.available_replicas or 0,
            }
            for deployment in (deployments.items or [])
        ]
    }