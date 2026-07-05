from app.services.ai.tools.base import BaseTool
from app.services.retrieval.retrieval_service import RetrievalService

class DocumentSearchTool(BaseTool):
    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service
        
    @property
    def name(self) -> str:
        return "search_documents"
        
    @property
    def description(self) -> str:
        return "Search the user's RAG knowledge base for specific documents, literature, code names, or concepts avoiding hallucinations."
        
    @property
    def parameters_schema(self) -> dict:
        return {"query": "string, exactly what to search for"}
        
    async def execute(self, execution_context: dict, query: str = "", **kwargs) -> str:
        user_id = execution_context.get("user_id")
        if not user_id:
            return "Execution error: Unknown user identity context."
            
        results = await self.retrieval_service.retrieve(query=query, user_id=user_id)
        if not results:
            return "No documents found."
            
        output = ""
        for r in results:
            doc_name = getattr(r.chunk.document, "title", None) or getattr(r.chunk.document, "filename", "Untitled")
            output += f"Document: {doc_name}\nContent: {r.chunk.content}\n\n---\n\n"
            
        return output
