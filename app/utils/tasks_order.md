**llm-validation**
    - An LLM semantically validates the alert request

**scraping**
    - Webscrape the active webscrape sources at each's given interval
        - docling_scraping
        - youtube_scraping

**vector-search**
    - Pgvector-search to see which alert-prompts are related to the scraped data
    - We also filter the data based on keyword

**llm-verification**
    - The related ones will be sent to an LLM to confirm if the data fulfills the alert
        - The prompt must not have been triggered nor expired, of course

**llm-generation**
    - If the data does satisfy the alert:
        - The LLM produces the alert in the alert-prompt's format

**alert-broadcasting**
    - We send the alert via HTTP request
        - In the alert-prompt's http method and url
        - And register the alert_event, of course