# News-Hook

A service for natural-language based alerts

**You setup alerts and we keep monitoring for when they happen**

The alerts requests come in what we call "alert prompts". Just like you'd say to a friend or assistant:
- "Inform me when [movie-name] gets a release date"
- "Tell me when [rumor] is either confirmed or denied"
- "Alert me on any tariffs news between USA and Brazil"

We might not know when and even if the alert will be fulfilled. The alert can be a one-time thing or recurring

**The alerts are triggered on user-created or webscraped data**

- When and if a document comes that fulfills an alert, we send the alert via http request

- It's a *natural-language webhook triggered by real-life news*

# How to run:

Make sure you have the .env file. Than:

```bash
.\venv\Scripts\activate
gcloud auth application-default login
```

That gcloud command will generate a application_default_credentials.json and give you the path for it in your computer
That file is needed for VertexAI authorization
On Windows, that path is "AppData\Roaming\gcloud". Copy that json to the root folder

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

After that, to generate the client-sdk for the front-end:
- Go to http://127.0.0.1:8000/openapi.json
- Save it to desktop
- Run ```openapi-generator-cli generate -i ../../../openapi.json -g typescript-axios -o client-sdk``` from the '/src' folder

For build-and-test-ing, you can run `build-and-test.bat` on Windows
For simple testing, you can run `pytest`

# What's the infrastructure

## Alert-Prompt / Alert-Request

- We get the POST request for an alert
    - An LLM validates the request based on semantic rules (must be clear, unambiguous, possible, etc). See "prompts.py" for that
- Valid requests will get stored
    - Their prompts will be vector-embedded
    - We extract keywords from them
- We keep monitoring
    - Periodically webscraping sources / Receiving user-created documents
    - Pgvector-search to see which alert-prompts are related to the scraped document
    - Keyword filtering
        - The document must contain at least one keyword extracted from the prompt
    - We ask an LLM for verification
        - The LLM confirms that the document fulfills the alert-request
    - We ask an LLM to generate a payload
    - We send the alert via HTTP request

# Pricing model

The cost for the alert-requests and events will be:
- The input and output tokens for:
    - The alert prompt
    - The documents sent by the user
    - The alert-sending / generation
- The api requests themselves