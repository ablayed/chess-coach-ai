import re


def _normalize_ocr_text(text: str) -> str:
    """Clean common OCR artifacts from DjVu/PDF text dumps before chunking."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00ad", "")
    # Merge hyphenated line-breaks that split words (e.g., "posi-\ntion").
    cleaned = re.sub(r"([A-Za-z])-\n([A-Za-z])", r"\1\2", cleaned)
    # Remove isolated page numbers / page labels.
    cleaned = re.sub(r"(?m)^\s*(?:Page\s+)?\d{1,4}\s*$", "", cleaned)
    # Remove bracketed page markers often found in OCR.
    cleaned = re.sub(r"(?m)^\s*\[\d{1,4}\]\s*$", "", cleaned)
    # Normalize excessive internal spacing.
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    # Collapse very large blank gaps.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _looks_like_chapter_heading(paragraph: str) -> bool:
    first_line = paragraph.split("\n", 1)[0].strip()
    return bool(
        re.match(
            r"^(CHAPTER|Chapter|PART|Part|BOOK|Book|LESSON|Lesson)\s+([IVXLCDM]+|\d+)",
            first_line,
        )
    )


def _looks_like_section_heading(paragraph: str) -> bool:
    first_line = paragraph.split("\n", 1)[0].strip()
    if not first_line or len(first_line) > 90:
        return False
    if first_line.isupper():
        return True
    if first_line.endswith((".", "!", "?")):
        return False
    # Title-style short headings are often section names in OCR books.
    words = first_line.split()
    title_case_words = sum(1 for w in words if w[:1].isupper())
    return len(words) <= 8 and title_case_words >= max(1, len(words) - 1)


def chunk_text(text: str, max_tokens: int = 600, overlap_tokens: int = 100) -> list[dict]:
    """Split text into overlapping chunks while respecting paragraph boundaries."""
    normalized = _normalize_ocr_text(text)
    paragraphs = re.split(r"\n\s*\n", normalized)

    chunks: list[dict] = []
    current_chunk = ""
    current_chapter: str | None = None
    current_section: str | None = None

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if _looks_like_chapter_heading(para):
            current_chapter = para.split("\n", 1)[0].strip()
            continue
        if _looks_like_section_heading(para):
            current_section = para.split("\n", 1)[0].strip()
            continue

        current_words = len(current_chunk.split())
        para_words = len(para.split())

        if current_chunk and (current_words + para_words > max_tokens):
            chunk_content = current_chunk.strip()
            chunks.append(
                {
                    "content": chunk_content,
                    "chapter": current_chapter,
                    "section": current_section,
                    "tokens": len(chunk_content.split()),
                }
            )
            chunk_words = chunk_content.split()
            overlap = " ".join(chunk_words[-overlap_tokens:]) if len(chunk_words) > overlap_tokens else ""
            current_chunk = f"{overlap}\n\n{para}" if overlap else para
        else:
            current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para

    if current_chunk.strip():
        final_content = current_chunk.strip()
        chunks.append(
            {
                "content": final_content,
                "chapter": current_chapter,
                "section": current_section,
                "tokens": len(final_content.split()),
            }
        )

    return chunks
