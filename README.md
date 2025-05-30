# news-hook
This is a platform to setup natural-language based alerts

# What the fuck is this?

This is a platform where you can setup natural-language based alerts
The alerts are triggered on webscraped data or user-created data


The alerts requests come in what we call "alert prompts". Just like you'd say to a friend:
- "Hey wake me up right before the game"
- "Hey, if Trump does do that please alert me"
- "Tell me if that gossip gets any updates"


- When and if a document comes that fulfills an alert, we send the alert via http request
- It's a *natural-language webhook triggered by real-life news*

# How to run:

```bash
docker run --name news-hook-db -e POSTGRES_DB=news_hook -e POSTGRES_USER=lendacerda -e POSTGRES_PASSWORD=l3ndacerda -p 5432:5432 -d ankane/pgvector:latest
```
Before proceeding, create the 'vector' extension in the db:
```bash
CREATE EXTENSION IF NOT EXISTS vector;
```
Than, run the server:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
_Note: The db will be on AWS at a later date..._

Also, to generate the client-sdk for the front-end, you just need to:
- Go in localhost:8000/docs
- Save the openai.json
- Run ```openapi-generator-cli generate -i ../../../openapi.json -g typescript-fetch -o client-sdk``` from the '/src' folder

For build-and-test-ing, you can run `build-and-test.bat` on Windows
For simple testing, you can run `pytest`

# What's the infrastructure

## Alert-Prompt/Alert-Request

- We get the POST request for an alert
    - An LLM validate the request (must be clear, unambiguous, possible, etc). See "prompts.py" for that
- Valid requests will get stored
    - Their prompts will be vector-embedded
- We keep monitoring
    - Periodically webscraping sources / Receiving user-created documents
    - Pgvector-search to see which alert-prompts are related to the scraped document
    - Keyword filtering
        - e.g if the alert-request is about a person and a country, we expect both their names in the scraped document
    - We ask an LLM for verification
        - The LLM confirms that the document fulfills the alert-request
    - If the document does satisfy the alert:
        - The LLM generates and sends an alert
        - This is a webhook, so we produce a payload in a given format
    - We send the alert via HTTP request
        - We of course register the alert_event

# Pricing model

The cost for the alert-requests and events will be:
- The input and output tokens for:
    - The alert creation
    - The documents sent by the user
    - The alert-sending
- The api request itself