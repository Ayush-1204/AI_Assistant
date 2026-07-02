import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Documents", "AI_Assistant", "apps", "api")))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models import Document, DocumentChunk, DocumentStatus

user_id = 1
embedding = [0.1] * 768

distance = DocumentChunk.embedding.cosine_distance(embedding).label("distance")

stmt = (
    select(DocumentChunk, distance)
    .join(Document)
    .where(
        Document.user_id == user_id,
        Document.status == DocumentStatus.READY,
    )
    .order_by(distance.asc())
    .limit(5)
    .options(selectinload(DocumentChunk.document))
)

from sqlalchemy.dialects import postgresql
compiled = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
with open("proper_sql.txt", "w", encoding="utf-8") as f:
    f.write(str(compiled))
