from abc import ABC, abstractmethod

from app.schemas.search import SearchResult


class SearchProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The identifier for this search provider"""
        pass

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> tuple[list[SearchResult], list[str]]:
        """Execute a search query and return a list of SearchResults alongside matched Image URLs"""
        pass
