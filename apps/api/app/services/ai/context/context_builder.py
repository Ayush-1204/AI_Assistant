from app.services.message_service import MessageService


class ContextBuilder:
    """
    Builds the conversational context that will be
    provided to the LLM.

    This class is intentionally isolated so future
    additions such as long-term memory, RAG,
    summarization, and tool outputs can be integrated
    without modifying AIService.
    """

    def __init__(
        self,
        message_service: MessageService,
    ):
        self.message_service = message_service

    async def build(
        self,
        conversation_id: int,
    ) -> list[dict]:
        """
        Build the context for a conversation.

        Current implementation:
        - Entire conversation history.

        Future:
        - Recent messages
        - Long-term memory
        - RAG documents
        - Tool outputs
        """

        return await self.message_service.get_history(
            conversation_id,
        )