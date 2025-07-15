import re
from langchain.document_loaders import PyPDFLoader


def clean_json(raw_text):
    match = re.search(r'\{.*\}',raw_text,re.DOTALL)
    if match:
        return match.group(0)
    else:
        return None
# Function to extract text from PDF
def extract_resume_text(pdf_file_path):
    loader = PyPDFLoader(pdf_file_path)
    pages = loader.load()
    return " ".join([page.page_content for page in pages])
