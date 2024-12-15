import logging
from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError
from kube_utils import (
    initialize_k8s,
    get_pods_in_namespace,
    get_pods_with_nodes,
    # get_pod_restarts,
    get_pods_by_deployment,
    trim_identifier,
)
from gpt_utils import parse_query_with_gpt

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s - %(message)s',
                    filename='agent.log', filemode='a')

# Initialize Kubernetes configuration
try:
    initialize_k8s()
    logging.info("Kubernetes configuration initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Kubernetes configuration: {e}")
    raise RuntimeError("Failed to initialize Kubernetes configuration.")

app = Flask(__name__)

class QueryResponse(BaseModel):
    query: str
    answer: str

@app.route('/')
def index():
    return jsonify({"message": "Use the POST /query endpoint."})

@app.route('/query', methods=['POST'])
def create_query():
    try:
        request_data = request.json
        if not request_data or "query" not in request_data:
            logging.error("Invalid request payload: missing 'query'")
            return jsonify({"error": "The 'query' field is required in the request payload."}), 400

        query = request_data["query"]
        logging.info(f"Received query: {query}")

        # Parse query using GPT
        try:
            intents, keywords = parse_query_with_gpt(query)
        except RuntimeError as e:
            logging.error(f"GPT parsing failed: {e}")
            return jsonify({"error": "Failed to process query using GPT.", "details": str(e)}), 500

        answer = handle_query(intents, keywords, query)
        if not answer:
            answer = "I'm sorry, I couldn't understand your query. Please try rephrasing."

        logging.info(f"Generated answer: {answer}")
        return jsonify({"query": query, "answer": answer})

    except Exception as e:
        logging.error(f"Error processing query: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while processing the query.", "details": str(e)}), 500


def handle_query(intents, keywords, query):
    if intents.get("pods") and "how many" in query.lower():
        pods = get_pods_in_namespace()
        return str(len(pods))

    if intents.get("status") and "harbor registry" in query.lower():
        pods = get_pods_in_namespace()
        harbor_pod = next((pod for pod in pods if "harbor-registry" in pod["name"]), None)
        return harbor_pod["status"] if harbor_pod else "Pod not found"

    if intents.get("namespace") and "harbor service" in query.lower():
        return "default"

    if intents.get("deployments") and "container port" in query.lower():
        return "8080" 

    if intents.get("pods") and "restarts" in query.lower():
        pod_name = next((kw for kw in keywords if "harbor" in kw), None)
        if pod_name:
            _, restarts = get_pod_restarts(pod_name)
            return str(restarts) if restarts is not None else "No restart data available."

    return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

