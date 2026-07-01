from abc import ABC, abstractmethod


class BaseVectorStore(ABC):

    @abstractmethod
    async def upsert(
        self,
        *,
        collection: str,
        point_id: str,
        vector: list[float],
        payload: dict,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        *,
        collection: str,
        vector: list[float],
        limit: int = 5,
    ) -> list[dict]:
        raise NotImplementedError