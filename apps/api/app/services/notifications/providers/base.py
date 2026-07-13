from abc import ABC, abstractmethod


class BaseNotificationProvider(ABC):
    @abstractmethod
    async def send(self, user_id: int, title: str, message: str, **kwargs) -> bool:
        pass
