from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import numpy as np
from .embedding_store import embedder

# Load tokenizer and model for BLOOM (causal language model)
tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-1b7")
model = AutoModelForCausalLM.from_pretrained("bigscience/bloom-1b7")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

def retrieve(query, faiss_index, texts, top_k=5):
    """Retrieve top_k relevant document chunks given a query."""
    query_emb = embedder.encode([query])
    distances, indices = faiss_index.search(np.array(query_emb), top_k)
    retrieved_texts = [texts[i] for i in indices[0]]
    return " ".join(retrieved_texts)

def generate_answer(context, query, max_new_tokens=256):
    inputs = tokenizer(
        f"Context: {context}\n\nQuestion: {query}\nAnswer:",
        return_tensors="pt",
        truncation=True,
        max_length=1024  # keep context under control
    )

    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,   # instead of max_length
        num_beams=3,
        no_repeat_ngram_size=2,
        early_stopping=True
    )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def rag_qa_pipeline(query, faiss_index, texts):
    """Full RAG pipeline: retrieve relevant chunks + generate answer."""
    context = retrieve(query, faiss_index, texts)
    answer = generate_answer(context, query)
    return answer
