from .base import BaseVectorStore


class QdrantVectorStore(
    BaseVectorStore,
):

    async def upsert(
        self,
        *,
        collection: str,
        point_id: str,
        vector: list[float],
        payload: dict,
    ) -> None:
        raise NotImplementedError

    async def search(
        self,
        *,
        collection: str,
        vector: list[float],
        limit: int = 5,
    ) -> list[dict]:
        raise NotImplementedError