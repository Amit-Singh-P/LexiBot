from transformers import pipeline

# Use a multilingual summarization model
summarizer = pipeline("summarization", model="google/mt5-small")

def summarize_text(text, max_length=150, min_length=50):
    """Generate summary for given text chunk."""
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']
