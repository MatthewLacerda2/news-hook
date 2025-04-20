import requests
from docling.document_converter import DocumentConverter

source = "https://tedboy.github.io/bs4_doc/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(source, headers=headers, timeout=15, retry=5) 

converter = DocumentConverter()

result = converter.convert(source)

print('-' * 5)
print(result.document.export_to_markdown())
input("Press Enter to continue...")
