"""Paragraph-aware text chunking for embedding.

Deterministic and dependency-free: packs whole paragraphs into chunks up to
max_chars, splitting only a paragraph that alone exceeds the limit.
"""

MAX_CHARS_DEFAULT = 400


def chunk_text(text: str, max_chars: int = MAX_CHARS_DEFAULT) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for start in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[start : start + max_chars])
            continue

        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks
