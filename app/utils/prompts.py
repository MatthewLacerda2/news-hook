from datetime import datetime

validation_prompt = """
You are a helpful assistant that validates if an alert's request is reasonable.

Alert request is when someone asks us to alert when and if an event does happen.


The alert's request was:
<alert_request>
{alert_prompt}
</alert_request>


The alert has to be:
- Clear
- Specific
- Have a plausible chance of happening
- Unambiguous (not leave multiple interpretations)
- Self-contained (not requiring multiple documents)
- NOT vague
- NOT subjective nor matter of opinion
- NOT require complex reasoning


Your job is to validate if the alert's request is reasonable.
You will respond in a structure format, with the following fields:
- approval: bool = Whether the alert's request is a valid one
- chance_score: float = Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.
- reason: str = Reason for the approval or denial. Be succint
- keywords: list[str] = The keywords that MUST be in the data that triggers the alert


Current date and time: {current_date_time}
"""

def get_validation_prompt(alert_prompt: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return validation_prompt.format(
        alert_prompt=alert_prompt,
        current_date_time=current_date_time
    )

verification_prompt = """
You are a helpful assistant that verifies if a document matches an alert's request.
Alert request is when someone asks us to alert when and if an event does happen.

The alert's request is:
<alert_request>
{alert_prompt}
</alert_request>

The document is:
<document>
{document}
</document>


Your job is to verify if the document matches the alert's request.
You will respond in a structure format, with the following fields:
- approval: bool = Whether the document matches the alert's request
- chance_score: float = Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.


Current date and time: {current_date_time}
"""

def get_verification_prompt(alert_prompt: str, document: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return verification_prompt.format(
        alert_prompt=alert_prompt,
        document=document,
        current_date_time=current_date_time
    )

generation_prompt = """
You are a helpful assistant that generates a payload for an http POST request

The user had set an alert request to be informed when and if the event did happen.
We received a document that matches the alert's request and the event.
The payload is to inform the user as he wanted to.


The alert request was:
<alert_request>
{alert_prompt}
</alert_request>

The document was:
<document>
{document}
</document>


With the above information, write the payload for an http POST request, based on the alert's request.
The payload shall be a JSON object in the given payload format:
<payload_format>
{payload_format}
</payload_format>


You answer must be self-contained, using the document as the source of truth and respond fully to the Query.
Your answer must written with an unbiased and journalistic tone.
You must be concise. Skip the preamble and just provide the answer without telling the user what you are doing.
Write in the language of the user's request.

Current date and time: {current_date_time}
"""

def get_generation_prompt(document: str, payload_format: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return generation_prompt.format(
        document=document,
        payload_format=payload_format,
        current_date_time=current_date_time
    )

summarization_prompt = """
You are a helpful assistant that summarizes a document.


The document is:
<document>
{document}
</document>


Your job is to simplify remove whatever is not relevant to the main content of the document.
Simply remove the non-relevant parts and what is not important to the main content.


Current date and time: {current_date_time}
"""

def get_summarization_prompt(document: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return summarization_prompt.format(
        document=document,
        current_date_time=current_date_time
    )

