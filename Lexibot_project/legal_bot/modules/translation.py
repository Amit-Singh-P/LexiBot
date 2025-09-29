from transformers import MarianMTModel, MarianTokenizer

def translate(text, src_lang, tgt_lang):
    model_name = f'Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}'
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    batch = tokenizer.prepare_seq2seq_batch([text], return_tensors="pt")
    generated = model.generate(**batch)
    return tokenizer.decode(generated[0], skip_special_tokens=True)
