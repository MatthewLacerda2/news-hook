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

For checking build-and-test-ing, you can just run the build-and-test.bat on Windows

# What's the infrastructure

## Alert-Prompt/Alert-Request

- We get the POST request for an alert
    - The request must obey rules (validity, possibility, unambiguity...)
- Valid requests will get stored
    - We store the metadata
    - They have their prompt vector-embedded
- We keep monitoring
    - Webscrape the active webscrape sources at each's given interval
    - Pgvector-search to see which alert-prompts are related to the scraped data
    - The related ones will be sent to an LLM to confirm if the data fulfills the alert
        - The prompt must not have been triggered nor expired, of course
    - If the data does satisfy the alert:
        - The LLM produces the alert in the alert-prompt's format
    - We send the alert via HTTP request
        - In the alert-prompt's http method and url
        - And register the alert_event, of course
- We check if the incoming data fits any alert
    - We check the embedding to quickly cull the alerts
    - We check metadata for quick validity
    - We use LLM to finalize the validation
- If it checks out, we process the data to send the appropriate alert

# Pricing model

The cost for the alert-requests and events will be:
- The api request
- The input and output tokens

The agent can select the LLMs for the alert request and response separately