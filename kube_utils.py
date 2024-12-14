from kubernetes import client, config
import os
import logging

def initialize_k8s():
    if "KUBECONFIG" in os.environ:
        logging.warning(f"Clearing pre-existing KUBECONFIG: {os.getenv('KUBECONFIG')}")
        del os.environ["KUBECONFIG"]

    kubeconfig_path = os.path.join(os.path.expanduser("~"), ".kube", "config")
    if not os.path.exists(kubeconfig_path):
        raise FileNotFoundError(f"Kubeconfig file not found at {kubeconfig_path}")
    
    config.load_kube_config(config_file=kubeconfig_path)
    logging.info(f"Kubernetes configuration initialized successfully. Resolved KUBECONFIG path: {kubeconfig_path}")

    # Log active context details
    contexts, active_context = config.list_kube_config_contexts()
    logging.info(f"Active Kubernetes context: {active_context}")
    logging.info(f"Kubernetes API server: {get_kubernetes_api_server()}")

def get_kubernetes_api_server():
    api_client = client.ApiClient()
    return api_client.configuration.host

def validate_namespace(namespace):
    if namespace != "validator-namespace":
        raise RuntimeError(f"Access to namespace '{namespace}' is not allowed.")

def get_pods_in_namespace(namespace="validator-namespace"):
    validate_namespace(namespace)
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(namespace)
    return [
        {
            "name": pod.metadata.name,
            "status": pod.status.phase,
            "restarts": sum(container.restart_count for container in pod.status.container_statuses or []),
        }
        for pod in pod_list.items
    ]

def get_pods_with_nodes(namespace="validator-namespace"):
    validate_namespace(namespace)
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(namespace)
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

def get_pod_restarts(pod_name, namespace="validator-namespace"):
    validate_namespace(namespace)
    logging.info(f"Fetching restart count for pod: {pod_name} in namespace: {namespace}")
    pods = get_pods_in_namespace(namespace)
    matched_pods = [pod for pod in pods if pod_name in pod["name"]]  

    if len(matched_pods) == 1:
        pod = matched_pods[0]
        trimmed_name = trim_identifier(pod["name"])  
        logging.info(f"Found pod '{pod['name']}' (trimmed to '{trimmed_name}'). Restarts: {pod['restarts']}")
        return trimmed_name, pod["restarts"]
    elif len(matched_pods) > 1:
        logging.warning(f"Multiple pods matched the name '{pod_name}': {[pod['name'] for pod in matched_pods]}")
        return None, None  
    else:
        logging.warning(f"No pods found matching the name '{pod_name}' in namespace '{namespace}'.")
        return None, None

def get_pods_by_deployment(deployment_name, namespace="validator-namespace"):
    validate_namespace(namespace)
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
        elif e.status == 403:
            logging.error(f"Permission denied when accessing namespace '{namespace}' for deployment '{deployment_name}'.")
            return []
        else:
            raise RuntimeError(f"Error fetching pods for deployment '{deployment_name}': {e}")

def log_cluster_resources():
    v1 = client.CoreV1Api()
    namespaces = [ns.metadata.name for ns in v1.list_namespace().items]
    logging.info(f"Available namespaces: {namespaces}")

    for namespace in namespaces:
        try:
            pods = [pod.metadata.name for pod in v1.list_namespaced_pod(namespace).items]
            logging.info(f"Pods in namespace '{namespace}': {pods}")
        except Exception as e:
            logging.warning(f"Error fetching pods in namespace '{namespace}': {e}")

def trim_identifier(name):
    return "-".join(name.split("-")[:-2]) if "-" in name else name
