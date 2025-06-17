#This is an utils function for project admins to send manually scraped documents

#It'll trigger alerts for any users
#It'll ask for a name, and then a content

import json
import requests

def manual_scraping():
    # Get the token from user
    print("Enter the token here ('gcloud auth print-identity-token'):")
    token = input("Token:")
    
    # Prompt for document details
    print("\nEnter document details:")
    name = input("Document name: ")
    print("Enter document content (press Enter twice to finish):")
    content_lines = []
    while True:
        line = input()
        if line == "" and content_lines and content_lines[-1] == "":
            break
        content_lines.append(line)
    content = "\n".join(content_lines[:-1])  # Remove the last empty line
    
    # Prepare the request
    #url = "https://newshookmvp-205743657377.southamerica-east1.run.app/api/v1/user_documents/manual"
    url = "http://127.0.0.1:8000/api/v1/user_documents/manual"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "content": content
    }
    
    # Print request details
    print("\nRequest:")
    print(json.dumps({
        "url": url,
        "headers": {k: v for k, v in headers.items() if k != "Authorization"},  # Hide token
        "data": data
    }, indent=2))
    
    # Make the request
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Print response
        print("\nResponse:")
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"\nError making request: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response text: {e.response.text}")

if __name__ == "__main__":
    manual_scraping()