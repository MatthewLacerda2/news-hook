# news-hook
A natural-language based alerts services

# What the fuck is this?

This is a platform for serving alerts, focused on AI agents

The alerts requests come in what we call "alert prompts". Just like you'd say on whatsapp:

- "Hey wake me up right before the game"
- "Hey, if Trump does do that please alert me"
- "Tell me if that gossip gets any updates"

The alert-prompt could come in json format, since those fit natural-language

- We get the alert
    - Verify if the alert is valid (hasn't happened already, it's even possible, isn't ambiguous/subjective/too-complex)
    - Alerts that need cross-referencing are not supported yet
    - Store it
- We continuously webscrape, sign-up to webhooks and send api-requests
- As we get those _news_, we check if any of them satisfy any alert-request
- If it does, we send the alert via http request

# How to run:

[insert-database-name]

```
pip install -r requirements.txt
docker-compose up -d
uvicorn main:app --reload
```

# What's the infrastructure

- We get the POST request for an alert
    - The request must obey rules (validity, possibility, unambiguity...)
- Valid requests will get stored
    - We store the metadata
    - They have their prompt vector-embedded
- We keep monitoring
    - Webscraping with docling, and LLM on top of that
    - Webhooks
    - Periodic GET requests (e.g news-api)
- We check if the incoming data fits any alert
    - We check the embedding to quickly cull the alerts
    - We check metadata for quick validity
    - We use LLM to finalize the validation
- If it checks out, we process the data to send the appropriate alert

# Types of alerts

- **Base**: includes data from webscraping only
    - Data from webscraping

- **Pro**:
    - Data from webscraping, webhooks, apis
    - Includes an LLM output response

- **Reasoning**:
    - Data from webscraping, webhooks, apis
    - Includes an LLM output response
    - Reasons on the intent of the alert'