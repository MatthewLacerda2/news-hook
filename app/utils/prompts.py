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
- Unambiguous
- Have a plausible chance of happening
- Self-contained (not requiring multiple documents)
- NOT vague
- NOT a matter of personal opinion or preference
- NOT require long reasoning


Your job is to validate if the alert's request is reasonable.
You will respond in a structure format, with the following fields:
- approval: bool = Is the alert's request valid?
- chance_score: float = Estimation of the quality of the request. Ranging from 0.0 to 1.0. Must be at least 0.85 to approve
- reason: str = Reason for the approval or denial. Be succinct
- keywords: list[str] = keywords required to be in the document that triggers the alert. Must be primitive, single words.


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
- approval: bool = Does the document match the alert's intent?
- chance_score: float = Estimation of the quality of the request. Ranging from 0.0 to 1.0. Must be at least 0.85 to approve
- reason: str = Reason for the approval or denial. Be succinct
- keywords: list[str] = keywords required to be in the document that triggers the alert, like name of a person, company


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
You are a helpful assistant that generate an information alert in a structured format.

The user had set an alert request to be informed when and if an event happens.
We received a document that matches the alert's request and the event did happen.
You will be given the alert request and the document that matches the alert's request.
Generate an information alert in a structured format.


The alert request was:
<alert_request>
{alert_prompt}
</alert_request>

The document was:
<document>
{document}
</document>

Your response must follow the user's requested payload format exactly:
<payload_format>
{payload_format}
</payload_format>


You answer must be self-contained, using the document as the source of truth and respond fully to the alert request.
Your answer must written with an unbiased and journalistic tone.
You must be succinct. Skip the preamble and just provide the answer without telling the user what you are doing.

Write in the language/dialect of the user's request.
If the alert request is in English, your response must be in English. If the alert request is in Spanish, your response must be in Spanish. And so on.

Current date and time: {current_date_time}
"""

def get_generation_prompt(document: str, payload_format: str, alert_prompt: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return generation_prompt.format(
        document=document,
        payload_format=payload_format,
        alert_prompt=alert_prompt,
        current_date_time=current_date_time
    )
