import re

from .memory_patterns import PATTERNS


class MemoryDetector:
    """
    Lightweight detector that determines whether
    a message should be sent to the LLM for
    structured memory extraction.

    This class SHOULD NOT perform any AI.
    """

    @staticmethod
    def should_extract(
        message: str,
    ) -> bool:

        text = message.lower().strip()

        for pattern in PATTERNS:

            if re.search(pattern, text):
                return True

        return False