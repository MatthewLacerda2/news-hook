#This is an utils function for project admins to send manually scraped documents

#It'll trigger alerts for any users
#It'll ask for a name, and then a content

import json
import requests
import sys
import os

def manual_scraping(filepath: str):
    # Validate file extension
    if not filepath.lower().endswith('.txt'):
        print("Error: Only .txt files are supported")
        sys.exit(1)
    
    # Get the API key from user
    print("Enter your API key:")
    api_key = input("API Key: ").strip()
    
    name : str = os.path.splitext(os.path.basename(filepath))[0]
    
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content : str = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    url = "http://127.0.0.1:8000/api/v1/user_documents/manual"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "content": content
    }
    
    print("\nRequest:")
    print(json.dumps({
        "url": url,
        "headers": {k: v for k, v in headers.items() if k != "X-API-Key"},
        "data": data
    }, indent=2))
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        print("\nResponse:")
        print(json.dumps(response.json(), indent=2)),
        
    except requests.exceptions.RequestException as e:
        print(f"\nError making request: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response text: {e.response.text}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python manual_scraping.py <filepath>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    manual_scraping(filepath)