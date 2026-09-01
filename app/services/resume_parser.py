import fitz
from docx import Document


def extract_pdf_text(file_path: str) -> str:
    document = fitz.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    return text


def extract_docx_text(file_path: str) -> str:
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)


def extract_resume_text(file_path: str, filename: str) -> str:
    filename = filename.lower()

    if filename.endswith(".pdf"):
        return extract_pdf_text(file_path)

    elif filename.endswith(".docx"):
        return extract_docx_text(file_path)

    else:
        raise ValueError("Only PDF and DOCX resumes are supported.")