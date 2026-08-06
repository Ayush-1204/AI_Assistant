import zipfile
import re
from pathlib import Path

from app.services.documents.models import ExtractedDocument
from .base import BaseExtractor


class DocxExtractor(BaseExtractor):
    """
    Extracts text content from .docx files natively without external dependencies.
    """

    async def extract(
        self,
        file_path: Path,
    ) -> ExtractedDocument:
        
        try:
            with zipfile.ZipFile(file_path, 'r') as docx_zip:
                xml_content = docx_zip.read('word/document.xml').decode('utf-8')
            
            # Basic XML tag stripper
            text = re.sub(r'<[^>]+>', ' ', xml_content)
            # Remove extra spaces
            text = re.sub(r'\s+', ' ', text).strip()
        except Exception:
            text = ""

        return ExtractedDocument(
            text=text,
            page_count=1,
            metadata={
                "source_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "filename": file_path.name,
                "file_size": file_path.stat().st_size if file_path.exists() else 0,
            },
            title=file_path.stem
        )
