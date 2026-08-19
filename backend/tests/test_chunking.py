from app.ingestion.chunking import chunk_text


def test_short_text_is_single_chunk():
    text = "This is a short syllabus paragraph."
    chunks = chunk_text(text, max_chars=800)
    assert chunks == [text]


def test_multiple_paragraphs_packed_until_limit():
    paragraphs = ["Paragraph one." * 10, "Paragraph two." * 10, "Paragraph three." * 10]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, max_chars=200)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 200 or "\n\n" not in chunk  # oversized single paragraphs are split alone


def test_oversized_single_paragraph_is_split():
    text = "word " * 500  # ~2500 chars, one paragraph
    chunks = chunk_text(text, max_chars=800)
    assert len(chunks) >= 3
    assert all(len(c) <= 800 for c in chunks)


def test_empty_text_yields_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n   ") == []
