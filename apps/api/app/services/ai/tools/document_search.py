from app.services.ai.memory import MemoryService
from app.services.ai.tools.base import BaseTool
from app.services.retrieval.retrieval_service import RetrievalService


class DocumentSearchTool(BaseTool):
    def __init__(self, retrieval_service: RetrievalService, memory_service: "MemoryService"):
        self.retrieval_service = retrieval_service
        self.memory_service = memory_service
        
    @property
    def name(self) -> str:
        return "search_documents"
        
    @property
    def description(self) -> str:
        return (
            "Search the user's RAG knowledge base for specific past documents, literature, code names, or concepts. "
            "CRITICAL: Do NOT use this tool if the user asks about a document they claim to have attached (e.g. 'what is in the pdf?'), "
            "but you do NOT see any '[Attached Document: ...]' in the current conversation context. In that case, "
            "just tell them to upload the document first."
        )
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Exactly what to search for"
                },
                "document_filename": {
                    "type": "string",
                    "description": "Optional filename to restrict the search to a specific document. Use this when the user explicitly asks to read or summarize a specific attached document."
                }
            },
            "required": ["query"]
        }
        
    async def execute(self, execution_context: dict, query: str = "", **kwargs) -> str:
        user_id = execution_context.get("user_id")
        if not user_id:
            return "Execution error: Unknown user identity context."
            
        document_filename = kwargs.get("document_filename")
        results = await self.retrieval_service.retrieve(
            query=query, 
            user_id=user_id,
            document_filename=document_filename
        )
        if not results:
            return "No documents found."
            
        output = ""
        chunks_text = []
        for r in results:
            doc_name = getattr(r.chunk.document, "title", None) or getattr(r.chunk.document, "filename", "Untitled")
            output += f"Document: {doc_name}\nContent: {r.chunk.content}\n\n---\n\n"
            chunks_text.append(r.chunk.content)
            
        import asyncio
        asyncio.create_task(
            self.memory_service.process_document_chunks(user_id, "\n\n".join(chunks_text))
        )
            
        return output
