import PyPDF2
import os

def extract_text_from_pdf(pdf_path, output_path=None):
    """
    Extract text from a PDF file and return a list of page texts.
    Optionally save the full text to a file.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File {pdf_path} does not exist.")

    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        extracted_pages = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text() or ""
            extracted_pages.append(text)
        full_text = "\n".join(extracted_pages)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as output_file:
                output_file.write(full_text)
        return extracted_pages
