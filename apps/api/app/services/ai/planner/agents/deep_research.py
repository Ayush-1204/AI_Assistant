import asyncio
import logging

from app.integrations.search.tavily import TavilySearchProvider
from app.services.ai.providers.router import ProviderRouter
from app.services.ai.tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)

class DeepResearchAgent:
    """
    Dedicated Multi-Hop planner explicitly designed to structure comprehensive 
    Markdown artifacts utilizing sequential web searches over generic conversational loops.
    """
    def __init__(self, router: ProviderRouter):
        self.router = router
        self.search_tool = WebSearchTool(TavilySearchProvider())

    async def run(self, query: str, context_messages: list[dict] | None = None) -> str:
        """Executes a deep multi-hop web scraping analysis pipeline."""
        
        memory_context = ""
        if context_messages and len(context_messages) > 0 and context_messages[0].get("role") == "system":
            sys_content = context_messages[0].get("content", "")
            if "=== RELEVANT MEMORIES ===" in sys_content:
                memory_parts = sys_content.split("=== RELEVANT MEMORIES ===")
                if len(memory_parts) > 1:
                    memory_context = "=== RELEVANT MEMORIES ===" + memory_parts[1].split("===")[0]

        # 1. Synthesize parallel search queries based on intent
        synthesis_prompt = f"""You are an elite Research Strategist. 
{memory_context}

Given the user query below, break it down into exactly three (3) distinct Google search queries that would yield the most comprehensive information to solve it.
Return ONLY a comma-separated list of the 3 text strings, without numbering. 
User Query: {query}"""
        
        try:
            query_results = await self.router._execute_with_router("chat", [{"role": "user", "content": synthesis_prompt}], intent="reasoning")
            if hasattr(query_results, 'text'):
                queries_text = query_results.text
            else:
                queries_text = str(query_results)
            
            queries = [q.strip() for q in queries_text.split(",")][:3]
        except Exception as e:
            logger.warning(f"Failed to generate search schema, falling back to raw query. {e}")
            queries = [query]

        logger.info(f"[DeepResearch] Executing multi-hop queries: {queries}")
        
        # 2. Execute parallel search abstractions
        search_tasks = [self.search_tool.execute(execution_context={}, query=q) for q in queries]
        search_reports = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        aggregated_context = ""
        for i, report in enumerate(search_reports):
            if isinstance(report, Exception):
                logger.error(f"[DeepResearch] Hop failure: {report}")
                continue
            aggregated_context += f"\\n--- SOURCE CHUNK {i} ---\\n{report}\\n"
            
        # 3. Final Formatted Generation
        final_prompt = f"""You are a specialized Deep Research agent.
{memory_context}

Using ONLY the following verified web excerpts, generate a highly comprehensive, academic-grade markdown report answering the original query.
IMPORTANT: You MUST include inline citation links mapping to the URLs provided in the excerpts!

User Query: {query}

Verified Excerpts:
{aggregated_context}
"""
        
        try:
            final_report = await self.router._execute_with_router("chat", [{"role": "system", "content": final_prompt}], intent="long_doc")
            if hasattr(final_report, 'text'):
                return final_report.text
            else:
                return str(final_report)
        except Exception as e:
            return f"An error occurred during deep compilation: {str(e)}"
