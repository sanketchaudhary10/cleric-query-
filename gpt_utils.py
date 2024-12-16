import openai
import os
import re
import logging
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set up OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API key is missing. Set it in the environment variables.")

def parse_query_with_gpt(query):
    prompt = f"""
        Parse the following query into intents and keywords, handling edge cases like unknown entities. Use this structure:
        {{
            "intents": {{
                "pods": true/false,
                "namespace": true/false,
                "status": true/false,
                "deployments": true/false,
                "logs": true/false
            }},
            "keywords": ["keyword1", "keyword2", ...]
        }}
        Examples:
        - Query: "How many pods are running in the default namespace?"
          Result: {{
              "intents": {{"pods": true, "namespace": true, "status": false, "deployments": false, "logs": false}},
              "keywords": ["pods", "default namespace"]
          }}
        Query: "{query}"
    """
    try:
        response_content = query_gpt(prompt)
        # logging.debug(f"Raw GPT-4 Response: {response_content}")

        # Remove the leading "Result:" text if present
        if response_content.strip().startswith("Result:"):
            response_content = response_content.strip()[7:].strip()

        response_data = safe_parse_gpt_response(response_content)
        if "intents" not in response_data or "keywords" not in response_data:
            raise ValueError("Missing required fields in GPT response.")

        logging.info(f"Parsed GPT Response: {response_data}")
        return response_data["intents"], response_data["keywords"]

    except Exception as e:
        logging.error(f"Error parsing query with GPT: {e}")
        raise RuntimeError("Failed to parse query using GPT.")

def query_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API Error: {e}")
        raise RuntimeError(f"Error querying GPT-4: {e}")

def extract_kubernetes_names(query):
    query_cleaned = re.sub(r"[^\w\s\-_]", "", query.lower())
    deployment_pattern = re.compile(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*")
    extracted_keywords = deployment_pattern.findall(query_cleaned)

    stop_words = {"how", "many", "has", "the", "had", "is"}
    filtered_keywords = [kw for kw in extracted_keywords if kw not in stop_words]

    logging.info(f"Extracted Kubernetes Names: {filtered_keywords}")
    return filtered_keywords

def safe_parse_gpt_response(response_content):
    try:
        # Attempt to locate JSON structure in the response
        start = response_content.find("{")
        end = response_content.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("No JSON structure found in GPT response.")
        
        # Extract potential JSON content
        json_content = response_content[start:end]
        
        # Attempt to load the extracted content as JSON
        response_data = json.loads(json_content)
        if "intents" not in response_data or "keywords" not in response_data:
            raise ValueError("Missing required fields in GPT response.")
        
        # logging.debug(f"Successfully parsed JSON from GPT response: {response_data}")
        return response_data

    except json.JSONDecodeError as e:
        logging.error(f"JSONDecodeError: {e}. Response Content: {response_content}")
        raise RuntimeError("GPT response was not in valid JSON format.")
    except Exception as e:
        logging.error(f"Error parsing GPT response: {e}. Response Content: {response_content}")
        raise RuntimeError("Failed to parse GPT response.")



# def extract_kubernetes_names(query):
#     query_cleaned = re.sub(r"[^\w\s\-_]", "", query.lower())
#     deployment_pattern = re.compile(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*")
#     extracted_keywords = deployment_pattern.findall(query_cleaned)

#     stop_words = {"how", "many", "has", "the", "had", "is"}
#     filtered_keywords = [kw for kw in extracted_keywords if kw not in stop_words]

#     logging.info(f"Extracted Kubernetes Names: {filtered_keywords}")
#     return filtered_keywords