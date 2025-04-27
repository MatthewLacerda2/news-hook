from datetime import datetime

validation_prompt = """
You are a helpful assistant that validates if an alert's request is reasonable.

Alert request is when someone asks us to alert when and if an event does happen.
The request carries a prompt and a parsed intent.


The alert's prompt is:
<alert_prompt>
{alert_prompt}
</alert_prompt>

The alert's parsed intent is:
<alert_parsed_intent>
{alert_parsed_intent}
</alert_parsed_intent>


The alerts have to be:
- Clear
- Specific
- Have a plausible chance of happening
- Unambiguous (not leave room for interpretation)
- Self-contained (not requiring multiple documents)
- NOT vague
- NOT subjective
- NOT require external tools or APIs


Your job is to validate if the alert's request is reasonable.
You will respond in a structure format, with the following fields:
- approval: Whether the alert's request is a valid one
- chance_score: Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.
- output_intent: What the LLM understood from the alert request
- keywords: The keywords that MUST be in the data that triggers the alert


Current date and time: {current_date_time}
"""

def get_validation_prompt(alert_prompt: str, alert_parsed_intent: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return validation_prompt.format(
        alert_prompt=alert_prompt,
        alert_parsed_intent=alert_parsed_intent,
        current_date_time=current_date_time
    )

verification_prompt = """
You are a helpful assistant that verifies if a document matches an alert's request.

Alert request is when someone asks us to alert when and if an event does happen.
The request carries a prompt and a parsed intent.


The alert's prompt is:
<alert_prompt>
{alert_prompt}
</alert_prompt>

The alert's parsed intent is:
<alert_parsed_intent>
{alert_parsed_intent}
</alert_parsed_intent>

The document is:
<document>
{document}
</document>


Your job is to verify if the document matches the alert's request.
You will respond in a structure format, with the following fields:
- approval: Whether the document matches the alert's request
- chance_score: Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.


Current date and time: {current_date_time}
"""

def get_verification_prompt(alert_prompt: str, alert_parsed_intent: str, document: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return verification_prompt.format(
        alert_prompt=alert_prompt,
        alert_parsed_intent=alert_parsed_intent,
        document=document,
        current_date_time=current_date_time
    )

generation_prompt = """
You are a helpful assistant that generates a payload for an http POST request

The user had set an alert request to be informed when and if the event did happen.
We received a document that matches the alert's request and the event.
The payload is to inform the user as he wanted to.


The alert request carried the parsed intent:
<alert_parsed_intent>
{alert_parsed_intent}
</alert_parsed_intent>

The document was:
<document>
{document}
</document>


With the above information, write the payload for an http POST request, based on the alert's request.
The payload shall be a JSON object in the given example format:
<example_payload>
{example_response}
</example_payload>


You answer must be self-contained, using the document as the source of truth and respond fully to the Query.
Your answer must written with an unbiased and journalistic tone.
You must be concise. Skip the preamble and just provide the answer without telling the user what you are doing.
Write in the language of the user's request.

Current date and time: {current_date_time}
"""

def get_generation_prompt(alert_parsed_intent: str, document: str, example_response: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return generation_prompt.format(
        alert_parsed_intent=alert_parsed_intent,
        document=document,
        example_response=example_response,
        current_date_time=current_date_time
    )
