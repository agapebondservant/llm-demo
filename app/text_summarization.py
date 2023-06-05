from app import crawler
from transformers import AutoTokenizer, TFAutoModelForSeq2SeqLM


def summarize_pdf(file_path: str):
    """
    Uses a pretrained model to perform text summarization on the file located at the given path
    :param file_path: Path to the file to be summarized
    :return: Text summary
    """
    content = crawler.extract_text_from_pdf(file_path)

    model = TFAutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
    tokenizer = AutoTokenizer.from_pretrained('facebook/bart-large-cnn')
    tokenizer.model_max_length = 1024  # sys.maxsize

    tokens_input = tokenizer.encode(f"summarize: {content}", return_tensors='tf', truncation=True)
    ids = model.generate(tokens_input, min_length=1000, max_length=2000)
    summary = tokenizer.decode(ids[0], skip_special_tokens=True)
    # summarizer = pipeline("summarization", max_length=500, model=model, tokenizer=tokenizer, truncation=True)
    return summary
