from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Initialize embedding model
embedder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

def create_embeddings(text, chunk_size=1000, chunk_overlap=200):
    if not text or len(text.strip()) == 0:
        raise ValueError("Input text is empty or blank")

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_text(text)

    if len(chunks) == 0:
        raise ValueError("Text split into zero chunks. Check chunk_size and input text.")

    # Create embeddings for each chunk
    embeddings = [embedder.encode(chunk) for chunk in chunks]

    # Stack to 2D numpy array
    embeddings_array = np.vstack(embeddings)

    return chunks, embeddings_array

def build_faiss_index(embedding_array):
    if embedding_array.ndim != 2:
        raise ValueError(f"Expected 2D array for embeddings but got shape {embedding_array.shape}")
    dimension = embedding_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embedding_array.astype(np.float32))
    return index

def save_faiss_index(index, file_path):
    faiss.write_index(index, file_path)

def load_faiss_index(file_path):
    return faiss.read_index(file_path)
