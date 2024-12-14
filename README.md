## Cleric Query Agent
The application is designed to handle user queries related to Kubernetes clusters by using OpenAI's GPT model. The project includes:

## Project Overview
- A Flask application that processes queries.
- Integration with OpenAI API for parsing and understanding queries.
- Kubernetes utilities to fetch relevant cluster data.


**Core Features**:
- Parse user queries using OpenAI's GPT model.
- Retrieve Kubernetes cluster information (e.g., pods, nodes, deployments).
- Handle specific intents like pod restarts, deployment details, and cluster status.

### Steps to Use Rufus

**1. Installation**:

## Cloning the Repository
```bash
git clone https://github.com/sanketchaudhary10/cleric-query-.git
cd cleric-query-
```

## Installing the required libraries
```bash
pip install -r requirements.txt
```
## Running the Application
**Step 1: Start the Flask Server**

**Run the application:**
```bash
python main.py
```

**You should see:**
```bash
Running on http://127.0.0.1:8000
```

## Project Structure
```
cleric-query-
├─ agent.log
├─ gpt_utils.py
├─ kube_utils.py
├─ main.py
├─ models.py
├─ README.md
└─ requirements.txt

```

## Approach
To solve this project, I aimed to create a query agent capable of interpreting natural language queries and retrieving relevant Kubernetes cluster information. The process involved integrating OpenAI's GPT model for query parsing and Kubernetes for fetching cluster data. My Approach:

## Understanding the Requirements: 

I broke down the requirements into three main components:

- Natural language processing using OpenAI GPT to identify user intents and keywords.
- Kubernetes utilities to fetch cluster data such as pods, nodes, and deployments.
- A Flask-based backend to serve the application and handle HTTP requests.

## Design and Implementation:

- gpt_utils.py: Handles query parsing using OpenAI's GPT.
- kube_utils.py: Interacts with Kubernetes APIs to fetch data such as pod statuses, restarts, and node information.
- developed a Flask application (main.py) that receives queries, processes them through GPT, and returns relevant Kubernetes data.

## Challenge: Mapping Natural Language Queries to Kubernetes Operations

Parsing natural language queries and mapping them to Kubernetes operations was challenging due to varying query structures and intents.

**Solution:** I initially used the spaCy model for quick prototyping and checking the query parsing ability of the model. Later, I switched to the required GPT-4 model. During this process I also tried a couple of GPT variants such as 4o-mini and 4o. Finally I decided to use the GPT-4 model for the query parser to identify key intents (e.g., "pods," "restarts," "status") and keywords (e.g., deployment names). This modular approach improved accuracy and simplified query mapping. Another challenging aspect of this project was handling the multiple cases associated with the kubernetes clusters. This included checking for key issues such as deployment-names, deployment-restarts, deployment-counts etc. To resolve this I created a simple modular code structure using exception handling to answer any edge cases.
