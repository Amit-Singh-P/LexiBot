import os
import mimetypes
import pytesseract
import fitz  # PyMuPDF
import cv2
import re
import tempfile
import textwrap
import time

# Voice & translation
import pyttsx3
import speech_recognition as sr
from deep_translator import GoogleTranslator

# ----------------- Voice Assistant -----------------
engine = pyttsx3.init()
recognizer = sr.Recognizer()

def detect_language(text):
    """Detect the language of a text using deep-translator"""
    try:
        detected = GoogleTranslator(source='auto', target='en').detect(text)
        return detected
    except Exception as e:
        print(f"⚠️ Language detection failed: {e}")
        return 'en'

def translate_text(text, target_lang='en'):
    """Translate text into target language"""
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        print(f"⚠️ Translation failed: {e}")
        return text

def speak(text, chunk_size=500, lang='en'):
    """
    Speak text with sentence-by-sentence pauses and optional translation.
    """
    if not text.strip():
        print("⚠️ Nothing to speak.")
        return

    # Translate if needed
    if lang != 'en':
        text = translate_text(text, target_lang=lang)

    # Split text into sentences for natural pauses
    sentences = re.split(r'(?<=[.!?]) +', text)
    for sentence in sentences:
        chunks = textwrap.wrap(sentence, chunk_size, break_long_words=False, replace_whitespace=False)
        for chunk in chunks:
            print(f"\n🔊 Speaking: {chunk}\n")
            engine.say(chunk)
            engine.runAndWait()
        time.sleep(0.3)  # short pause between sentences

def listen(timeout=5, phrase_time_limit=10):
    """
    Listen to user's voice and return recognized text and detected language.
    Returns: (text, detected_language)
    """
    with sr.Microphone() as source:
        print("🎤 Listening... Please speak now.")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = recognizer.recognize_google(audio)
            lang_detected = detect_language(text)
            print(f"📝 User said: {text} (Language detected: {lang_detected})")
            return text, lang_detected
        except sr.WaitTimeoutError:
            print("⚠️ Listening timed out.")
        except sr.UnknownValueError:
            print("⚠️ Could not understand audio.")
        except sr.RequestError as e:
            print(f"⚠️ Speech recognition error: {e}")
    return "", "en"

# ----------------- Legal Document Reader -----------------
def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"⚠️ Could not load image: {image_path}")
    img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    img = cv2.medianBlur(img, 3)
    return img

def extract_text_from_image(image_path):
    img = preprocess_image(image_path)
    text = pytesseract.image_to_string(img, lang="eng")
    return clean_text(text)

def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text("text")
        if page_text.strip():
            text += f"\n--- Page {page_num+1} ---\n{clean_text(page_text)}\n"
        else:
            pix = page.get_pixmap(dpi=300)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                tmp_img.write(pix.tobytes("png"))
                tmp_img_path = tmp_img.name
            ocr_text = extract_text_from_image(tmp_img_path)
            text += f"\n--- Page {page_num+1} (OCR) ---\n{ocr_text}\n"
            os.remove(tmp_img_path)
    return text.strip()

def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def load_document(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and "pdf" in mime_type:
        return extract_text_from_pdf(file_path)
    elif mime_type and ("jpeg" in mime_type or "png" in mime_type):
        return extract_text_from_image(file_path)
    else:
        raise ValueError("Unsupported file type. Use PDF, JPG, or PNG.")

# ----------------- Main Bot -----------------
if __name__ == "__main__":
    from modules import embedding_store, rag_qa, chat_memory

    # Load document
    file_path = input("Enter PDF/JPG/PNG path: ").strip()
    try:
        raw_text = load_document(file_path)
    except Exception as e:
        print(f"❌ Error loading document: {e}")
        exit()

    clean_doc_text = clean_text(raw_text)
    speak("Document loaded successfully. Creating embeddings...")

    # Embeddings & FAISS index
    chunks, embeddings = embedding_store.create_embeddings(clean_doc_text)
    faiss_index = embedding_store.build_faiss_index(embeddings)
    speak("Embeddings created. Ready for your questions.")

    # Setup chat memory
    memory = chat_memory.ChatMemory()

    speak("Hello! I am your smarter legal voice assistant. Ask me anything about the document.")

    # Conversation loop
    while True:
        query, user_lang = listen()
        if not query:
            continue
        if query.lower() in ['exit', 'quit', 'bye']:
            speak("Goodbye! Have a nice day.", lang=user_lang)
            break

        # Get answer from RAG-QA
        answer = rag_qa.rag_qa_pipeline(query, faiss_index, chunks)
        memory.add(query, answer)

        # Speak summary or answer
        if "summary" in query.lower():
            speak("Here is the summary of the document:", lang=user_lang)
            speak(clean_doc_text, lang=user_lang)
        else:
            speak("Here is the answer to your question:", lang=user_lang)
            speak(answer, lang=user_lang)
