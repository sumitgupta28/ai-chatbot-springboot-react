def extract_text_from_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")
