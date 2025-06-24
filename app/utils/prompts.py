from datetime import datetime

validation_prompt = """
You are a helpful assistant that validates whether an alert request is reasonable.
An alert request is when someone asks to be notified if and when a specific event happens.


The alert request is:
<alert_request>
{alert_prompt}
</alert_request>


A valid alert request must meet the following criteria:
- Clear
- Specific
- Unambiguous
- Has a plausible chance of occurring
- Self-contained (does not require multiple documents to verify)
- NOT vague
- NOT based on personal opinion or preference
- NOT require long or complex reasoning

Your job is to validate whether the alert request is reasonable.

Respond using the following structured format:
- approval: bool — Is the alert request valid?
- chance_score: float — Estimated quality of the request, from 0.0 to 1.0. Must be ≥ 0.85 to approve.
- reason: str — Succinct justification of the approval or denial.
- keywords: list[str] — Primitive, single-word keywords that must be present in the triggering document.

Current date and time: {current_date_time}
"""


def get_validation_prompt(alert_prompt: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return validation_prompt.format(
        alert_prompt=alert_prompt,
        current_date_time=current_date_time
    )

verification_prompt = """
You are a helpful assistant that verifies whether a document matches an alert request.
An alert request is when someone asks to be notified if and when a specific event happens.


The alert request is:
<alert_request>
{alert_prompt}
</alert_request>

The document is:
<document>
{document}
</document>


Your job is to verify whether the document matches the alert request.

Respond using the following structured format:
- approval: bool — Does the document match the alert request?
- chance_score: float — Estimated quality of the match, from 0.0 to 1.0. Must be ≥ 0.9 to approve.
- reason: str — Briefly explain your decision. Be as succinct and short as possible.
- keywords: list[str] — Primitive, single-word keywords that must be present in the triggering document.

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
You will be given the alert request and the document that matches the alert request.


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


Your alert must be self-contained, using the document as the source of truth and respond fully to the alert request.
Your alert must be written with an unbiased and journalistic tone.
You must be succinct. Skip the preamble and just provide the alert without telling the user what you are doing.
Write in the language/dialect of the user's request.

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
