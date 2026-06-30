class PromptBuilder:
    """
    Centralized prompt templates for all AI tasks.
    """

    @staticmethod
    def chat(
        messages: list[dict],
    ) -> str:
        """
        Convert conversation history into a prompt.
        """

        return "\n".join(
            f"{message['role']}: {message['content']}"
            for message in messages
        )

    @staticmethod
    def title(
        first_message: str,
    ) -> str:
        """
        Build a prompt for conversation title generation.
        """

        return f"""
Generate a concise conversation title.

Rules:
- Maximum 5 words
- No quotation marks
- No punctuation
- Title Case
- Return ONLY the title

User Message:

{first_message}
"""