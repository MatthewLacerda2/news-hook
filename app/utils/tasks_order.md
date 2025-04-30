**llm_validator**
    - An LLM validates the alert request

**../tasks**
    - Webscrape the active webscrape sources at each's given interval
        - docling_scraping
        - youtube_scraping

**vector_search**
    - First we filter the alerts by those whose keywords are found in the document
    - Vector-search to see which alert-prompts are related to the document

**llm_verification**
    - The related ones will be sent to an LLM to confirm if the data fulfills the alert
        - The prompt must not have been triggered nor expired, of course

**llm_generation**
    - If the data does satisfy the alert:
        - The LLM produces the alert in the alert-prompt's format

**alert_broadcasting**
    - We send the alert-event's HTTP request
        - In it's url, method, header and payload
        - And register the alert_event, of course