# Task Order

## LLM Validator
- An LLM validates the alert request

## Monitoring
- Webscrape the active webscrape sources at each's given interval
  - docling_scraping
  - youtube_scraping
OR
- Receive documents sent by the user

## Vector Search
- First we filter the alerts by those whose keywords are found in the document
- Vector-search to see which alert-prompts are related to the document

## LLM Verification
- The related ones will be sent to an LLM to confirm if the data fulfills the alert
  - The prompt must not have been triggered nor expired, of course

## LLM Generation
- If the data does satisfy the alert:
  - The LLM produces the alert in the alert-prompt's format

## Alert Broadcasting
- We send the alert-event's HTTP request
  - In its url, method, header and payload
  - And register the alert_event, of course