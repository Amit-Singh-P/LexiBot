import os
import mimetypes
import pytesseract
import fitz  # PyMuPDF
import cv2
import re
import tempfile

# ---------- Preprocess image for better OCR ----------
def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"⚠️ Could not load image: {image_path}")
    # Increase contrast and binarize
    img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # Remove noise
    img = cv2.medianBlur(img, 3)
    return img

# ---------- OCR on images ----------
def extract_text_from_image(image_path):
    img = preprocess_image(image_path)
    text = pytesseract.image_to_string(img, lang="eng")
    return clean_text(text)

# ---------- Extract text from PDF ----------
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Try native text extraction
        page_text = page.get_text("text")
        if page_text.strip():
            text += f"\n--- Page {page_num+1} ---\n{clean_text(page_text)}\n"
        else:
            # Fallback to OCR on page image
            pix = page.get_pixmap(dpi=300)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                tmp_img.write(pix.tobytes("png"))
                tmp_img_path = tmp_img.name

            ocr_text = extract_text_from_image(tmp_img_path)
            text += f"\n--- Page {page_num+1} (OCR) ---\n{ocr_text}\n"
            os.remove(tmp_img_path)

    return text.strip()

# ---------- Cleanup OCR/Text Output ----------
def clean_text(text):
    # Remove weird symbols and excessive whitespace
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # remove non-ASCII
    text = re.sub(r'\s+', ' ', text)  # normalize spaces
    return text.strip()

# ---------- Master function ----------
def read_document(file_path):
    if not os.path.exists(file_path):
        return f"❌ File not found: {file_path}"

    mime_type, _ = mimetypes.guess_type(file_path)

    if mime_type and "pdf" in mime_type:
        return extract_text_from_pdf(file_path)
    elif mime_type and ("jpeg" in mime_type or "png" in mime_type):
        return extract_text_from_image(file_path)
    else:
        return "❌ Unsupported file type. Please provide a PDF, JPG, or PNG."

# ---------- Wrapper for pipeline ----------
def load_document(file_path):
    """Wrapper for use in test.py"""
    return read_document(file_path)


# file_path = "/Applications/Projects/LexiBot/Lexibots_project/legal_bot/data/1.jpg"  
