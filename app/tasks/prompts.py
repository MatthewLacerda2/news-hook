from datetime import datetime

validation_prompt = """
You are a helpful assistant that validates if an alert's request is reasonable.

We have an alert request, to monitor and inform when and if an event happens.
The request carries a prompt and a parsed intent.

The alert's prompt is:
<alert_prompt>
{alert_prompt}
</alert_prompt>

The alert's parsed intent is:
<alert_parsed_intent>
{alert_parsed_intent}
</alert_parsed_intent>

As guidelines, the alert request must be:
- Clear
- Specific
- Have a plausible chance of happening
- Unambiguous (not leave room for interpretation)
- NOT vague
- NOT subjective
- NOT require external tools or APIs

Your job is to validate if the alert's request is reasonable.
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

We have an alert request, to monitor and inform when and if an event happens.
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

With the above information, verify if the document matches the alert's request.
If so, we will trigger the alert and send a request to the alert's URL.

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
You are a helpful assistant that generates a payload for an http request, based on an alert's request.

We had an alert request, to monitor and inform when and if an event happens.
Another system has done the work of verifying if document matches the alert's request.
The request carried the parsed intent:
<alert_parsed_intent>
{alert_parsed_intent}
</alert_parsed_intent>

The document was:
<document>
{document}
</document>

With the above information, write an accurate and comprehensive payload for an http request, based on the alert's request.
The payload shall be a JSON object in the given example format:
<example_payload>
{example_response}
</example_payload>

You answer must be self-contained, using the document as the source of truth and respond fully to the Query.
Your answer must be correct, high-quality, and written by an expert using an unbiased and journalistic tone.
Remember you must be concise! Skip the preamble and just provide the answer without telling the user what you are doing.
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
