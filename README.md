# news-hook
This is a platform for sending alerts, focused mainly on AI agents

# What the fuck is this?

This is a platform for sending alerts, focused mainly on AI agents
The alerts requests come in what we call "alert prompts". Just like you'd say to a friend:

- "Hey wake me up right before the game"
- "Hey, if Trump does do that please alert me"
- "Tell me if that gossip gets any updates"

The alert-prompt could come in json format, since those fit natural-language

- When and if the event happens, we send the alert via http request
- It's a *natural-language triggered webhook*

# How to run:

## Database Setup (Local Development)
1. Start PostgreSQL using Docker:
```bash
docker run --name news-hook-db \
    -e POSTGRES_DB=news_hook \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -p 5432:5432 \
    -d postgres:latest
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the application:
```bash
uvicorn app.main:app --reload
```

_Note: The db will be on AWS at a later date..._

For build-and-test-ing, you can run `build-and-test.bat` on Windows
For simple testing, you can run `pytest`

# What's the infrastructure

## Alert-Prompt/Alert-Request

- We get the POST request for an alert
    - The request must obey semantic rules (clarity, possibility, unambiguity...). See "prompts.py" for that
    - An LLM will validate those semantic rules
- Valid requests will get stored
    - Their prompts will be vector-embedded
- We keep monitoring
    - Periodically webscraping sources
    - Pgvector-search to see which alert-prompts are related to the scraped document
    - Keyword filtering
        - e.g if the alert-request is about a person and a country, we expect both their names in the scraped document
    - We ask an LLM LLM for verification
        - The LLM compares the alert-request and the document to see if the alert should be triggered
    - If the document does satisfy the alert:
        - The LLM produces it
        - This is a webhook, so we produce a payload in a given format
    - We send the alert via HTTP request
        - In the alert-prompt's http method, url and format
        - We of course register the alert_event

# Pricing model

The cost for the alert-requests and events will be:
- The input and output tokens for the model used
- The api request itself

The agent can select the LLMs for the alert request and response separately
We just pass forward the cost of the llm. What we are profiting on is the cost of our own infrastructure