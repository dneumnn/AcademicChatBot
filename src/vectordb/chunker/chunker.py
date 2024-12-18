import nltk

nltk.download('punkt')

def load_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

def save_chunks(chunks, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for i, chunk in enumerate(chunks):
            file.write(f"Chunk {i+1}:\n{chunk}\n\n")

def chunk_text_nltk(text, max_sentences_per_chunk, overlap_sentences):
    paragraphs = nltk.tokenize.blankline_tokenize(text)
    chunks = []
    for i, paragraph in enumerate(paragraphs):
        sentences = nltk.sent_tokenize(paragraph)
        j = 0
        while j < len(sentences):
            start = j
            end = start + max_sentences_per_chunk
            chunk_sentences = sentences[start:end]
            if (i != 0 or j != 0) and overlap_sentences > 0:
                if j == 0:
                    prev_sentences = nltk.sent_tokenize(paragraphs[i - 1])
                    overlap = prev_sentences[-overlap_sentences:]
                else:
                    overlap = sentences[start - overlap_sentences:start]
                chunk_sentences = overlap + chunk_sentences
            chunk = ' '.join(chunk_sentences)
            chunks.append(chunk)
            j += max_sentences_per_chunk
    return chunks

# def chunk_text_hf(text, max_sentences_per_chunk, overlap_sentences):
    summarizer = pipeline("summarization")
    paragraphs = nltk.tokenize.blankline_tokenize(text)
    chunks = []
    for i, paragraph in enumerate(paragraphs):
        sentences = nltk.sent_tokenize(paragraph)
        j = 0
        while j < len(sentences):
            start = j
            end = start + max_sentences_per_chunk
            chunk_sentences = sentences[start:end]
            if (i != 0 or j != 0) and overlap_sentences > 0:
                if j == 0:
                    prev_sentences = nltk.sent_tokenize(paragraphs[i - 1])
                    overlap = prev_sentences[-overlap_sentences:]
                else:
                    overlap = sentences[start - overlap_sentences:start]
                chunk_sentences = overlap + chunk_sentences
            chunk = ' '.join(chunk_sentences)
            summarized_chunk = summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
            chunks.append(summarized_chunk)
            j += max_sentences_per_chunk
    return chunks


