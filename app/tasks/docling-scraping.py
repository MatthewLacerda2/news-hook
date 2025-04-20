import requests
from docling.document_converter import DocumentConverter

source = "https://tedboy.github.io/bs4_doc/"

response = requests.get(source)

converter = DocumentConverter()

result = converter.convert(source)

print('-' * 5)
print(result.document.export_to_markdown())
input("Press Enter to continue...")
