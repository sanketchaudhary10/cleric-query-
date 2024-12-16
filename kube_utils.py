from kubernetes import client, config
import os
import logging

def initialize_k8s():
    kubeconfig_path = os.getenv("KUBECONFIG", os.path.join(os.path.expanduser("~"), ".kube", "config"))
    if not os.path.exists(kubeconfig_path):
        raise FileNotFoundError(f"Kubeconfig file not found at {kubeconfig_path}")
    
    config.load_kube_config(config_file=kubeconfig_path)    
    logging.info(f"KUBECONFIG in use: {os.getenv('KUBECONFIG')} (Resolved Path: {kubeconfig_path})")

def get_pods_in_namespace(namespace="default", label_selector=None):
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(namespace, label_selector=label_selector)
    logging.info(f"Fetched {len(pod_list.items)} pods from namespace '{namespace}'.")
    return [
        {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "restarts": sum(container.restart_count for container in pod.status.container_statuses or []),
        }
        for pod in pod_list.items
    ]

def get_cluster_nodes():
    v1 = client.CoreV1Api()
    nodes = v1.list_node()
    logging.info(f"Fetched {len(nodes.items)} nodes in the cluster.")
    return [
        {
            "name": node.metadata.name,
            "labels": node.metadata.labels
        }
        for node in nodes.items
    ]

def get_pods_with_nodes(namespace="default", label_selector=None):
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(namespace, label_selector=label_selector)
    pods_with_nodes = []
    for pod in pod_list.items:
        if pod.spec.node_name:
            pods_with_nodes.append({
                "name": pod.metadata.name,
                "node": pod.spec.node_name,
                "status": pod.status.phase,
            })
        else:
            logging.warning(f"Pod {pod.metadata.name} does not have a nodeName assigned.")
    return pods_with_nodes

def get_pods_by_deployment(deployment_name, namespace="default"):
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    try:
        deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)
        selector = deployment.spec.selector.match_labels
        label_selector = ",".join([f"{key}={value}" for key, value in selector.items()])
        logging.info(f"Namespace: {namespace}, Label selector for deployment '{deployment_name}': {label_selector}")

        pod_list = v1.list_namespaced_pod(namespace, label_selector=label_selector)
        pods = [
            {"name": pod.metadata.name, "status": pod.status.phase}
            for pod in pod_list.items
        ]
        logging.info(f"Pods found for deployment '{deployment_name}': {[pod['name'] for pod in pods]}")
        return pods
    except client.exceptions.ApiException as e:
        if e.status == 404:
            logging.warning(f"Deployment '{deployment_name}' not found in namespace '{namespace}'.")
            return []
        raise RuntimeError(f"Error fetching pods for deployment '{deployment_name}': {e}")

def trim_identifier(name):
    return "-".join(name.split("-")[:-2]) if "-" in name else name
