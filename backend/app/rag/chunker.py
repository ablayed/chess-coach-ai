import re


def chunk_text(text: str, max_tokens: int = 600, overlap_tokens: int = 100) -> list[dict]:
    """Split text into overlapping chunks, respecting paragraph boundaries."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    chunks: list[dict] = []
    current_chunk = ""
    current_chapter: str | None = None
    current_section: str | None = None

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if re.match(r"^(CHAPTER|Chapter|PART|Part)\s+[IVXLCDM\d]+", para):
            current_chapter = para.split("\n")[0].strip()
            continue
        if len(para) < 80 and para.isupper():
            current_section = para.strip()
            continue

        word_count = len(current_chunk.split())
        para_words = len(para.split())

        if word_count + para_words > max_tokens and current_chunk:
            chunks.append(
                {
                    "content": current_chunk.strip(),
                    "chapter": current_chapter,
                    "section": current_section,
                    "tokens": len(current_chunk.split()),
                }
            )
            words = current_chunk.split()
            overlap = " ".join(words[-overlap_tokens:]) if len(words) > overlap_tokens else ""
            current_chunk = overlap + "\n\n" + para if overlap else para
        else:
            current_chunk += "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(
            {
                "content": current_chunk.strip(),
                "chapter": current_chapter,
                "section": current_section,
                "tokens": len(current_chunk.split()),
            }
        )

    return chunks
