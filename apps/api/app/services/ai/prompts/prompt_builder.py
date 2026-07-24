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

        lines = []
        import json
        for message in messages:
            if 'content' in message:
                lines.append(f"{message.get('role', 'user')}: {message['content']}")
            else:
                lines.append(f"{message.get('role', 'user')}: {json.dumps(message.get('parts', message))}")
        return "\n".join(lines)

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