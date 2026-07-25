import json
import logging
import urllib.parse
from typing import Any
import xml.etree.ElementTree as ET
import httpx

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class ArxivTool(BaseTool):
    """
    Searches the arXiv API for academic papers and preprints.
    """

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return "arxiv_search"

    @property
    def description(self) -> str:
        return (
            "Searches arXiv for academic papers, specifically in physics, mathematics, "
            "computer science (including AI/ML), quantitative biology, and quantitative finance. "
            "Returns titles, authors, published dates, and abstracts."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, e.g., 'large language models', 'quantum computing', or author names."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of papers to retrieve (default is 5, max 10).",
                    "default": 5
                }
            },
            "required": ["query"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        query = kwargs.get("query")
        if not query:
            return "Error: 'query' parameter is required."
            
        max_results = min(kwargs.get("max_results", 5), 10)

        try:
            headers = {"User-Agent": "AntigravityPersonalAssistant/1.0 (https://github.com; contact@example.com)"}
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
                url = f"https://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}"
                response = await client.get(url)
                response.raise_for_status()
                
                # Parse the XML response (Atom feed format)
                root = ET.fromstring(response.text)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                papers = []
                for entry in root.findall('atom:entry', ns):
                    title_elem = entry.find('atom:title', ns)
                    summary_elem = entry.find('atom:summary', ns)
                    published_elem = entry.find('atom:published', ns)
                    id_elem = entry.find('atom:id', ns)
                    
                    # Extract page URL
                    paper_url = ""
                    for link in entry.findall('atom:link', ns):
                        if link.attrib.get('type') == 'text/html' or link.attrib.get('rel') == 'alternate':
                            paper_url = link.attrib.get('href', '')
                            break
                    if not paper_url and id_elem is not None:
                        paper_url = id_elem.text or ""
                    
                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name_elem = author.find('atom:name', ns)
                        if name_elem is not None and name_elem.text:
                            authors.append(name_elem.text.strip())
                    
                    raw_title = title_elem.text if title_elem is not None and title_elem.text else ""
                    clean_title = " ".join(raw_title.split())
                    
                    raw_summary = summary_elem.text if summary_elem is not None and summary_elem.text else ""
                    clean_summary = " ".join(raw_summary.split())
                    
                    papers.append({
                        "title": clean_title,
                        "published": published_elem.text if published_elem is not None else "",
                        "authors": authors,
                        "summary": clean_summary,
                        "url": paper_url
                    })
                
                if not papers:
                    return f"No arXiv papers found for '{query}'."
                    
                return json.dumps(papers)

        except Exception as e:
            logger.error(f"[ArxivTool] Request failed: {str(e)}")
            return f"Error executing arXiv search: {str(e)}"
