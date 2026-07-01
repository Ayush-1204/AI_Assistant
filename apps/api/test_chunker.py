from pathlib import Path

from app.services.documents.chunking.text_chunker import (
    TextChunker,
)

text = Path("sample.txt").read_text(
    encoding="utf-8"
)

chunker = TextChunker()

chunks = chunker.chunk(text)

print(len(chunks))

for c in chunks:

    print("=" * 80)

    print(c["chunk_index"])

    print(c["token_count"])

    print(c["content"][:200])