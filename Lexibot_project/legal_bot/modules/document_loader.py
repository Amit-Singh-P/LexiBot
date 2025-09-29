import pdfplumber
import pytesseract
from PIL import Image
import io

def load_pdf_text(file_path):
    """Load text from a pdf file using pdfplumber."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def ocr_pdf_image(image_bytes):
    """Extract text from an image using Tesseract."""
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)

def load_scanned_pdf_with_ocr(file_path):
    """Extract text from scanned PDF using OCR - page images to text."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_image = page.to_image(resolution=300)
            text += ocr_pdf_image(page_image.original.bytes) + "\n"
    return text
