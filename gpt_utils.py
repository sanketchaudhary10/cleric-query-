import openai
import os
import json
import logging


# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    logging.error("OpenAI API key is missing. Set it in the environment variables.")
    raise ValueError("OpenAI API key is missing. Set it in the environment variables.")

def parse_query_with_gpt(query):
    prompt = f"""
        Parse the following query into intents and keywords. Structure:
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
        Query: "{query}"
    """
    try:
        response_content = query_gpt(prompt)
        logging.info(f"GPT-4 Response: {response_content}")

        if response_content.strip().startswith("Result:"):
            response_content = response_content.strip()[7:].strip()

        response_data = json.loads(response_content)
        
        if not isinstance(response_data, dict):
            raise ValueError("GPT response is not a valid dictionary.")
        if "intents" not in response_data or "keywords" not in response_data:
            raise ValueError("Missing required fields in GPT response.")
        if not isinstance(response_data["intents"], dict) or not isinstance(response_data["keywords"], list):
            raise ValueError("Invalid data types for 'intents' or 'keywords' in GPT response.")

        return response_data["intents"], response_data["keywords"]

    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse GPT response as JSON: {e}")
        raise RuntimeError("GPT response was not in valid JSON format.")
    except Exception as e:
        logging.error(f"Error parsing query with GPT: {e}")
        raise RuntimeError("Failed to parse query using GPT-4.")

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
