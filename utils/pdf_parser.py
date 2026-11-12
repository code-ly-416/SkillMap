import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    # Extracts and concatenates text from all pages of an uploaded PDF file.
    # Returns "" when the file cannot be read so callers can handle the failure.
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
