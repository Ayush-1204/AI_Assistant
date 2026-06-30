import re


class MemoryDetector:
    """
    Detect whether a message contains
    long-term memory worth storing.
    """

    PATTERNS = [
        # Personal
        r"\bmy name is\b",
        r"\bi am\b",
        r"\bi'm\b",
        r"\bmy birthday\b",

        # Education / Work
        r"\bi study\b",
        r"\bi work\b",

        # Preferences
        r"\bi prefer\b",
        r"\bmy favorite\b",
        r"\bmy favourite\b",
        r"\bi like\b",
        r"\bi dislike\b",

        # Goals
        r"\bi want to\b",
        r"\bi plan to\b",
        r"\bmy goal\b",

        # Explicit memory
        r"\bremember\b",
        r"\bdon't forget\b",
    ]

    @classmethod
    def should_extract(
        cls,
        message: str,
    ) -> bool:

        message = message.lower()

        for pattern in cls.PATTERNS:
            if re.search(pattern, message):
                return True

        return False