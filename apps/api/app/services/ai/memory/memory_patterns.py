"""
Rule-based patterns used to determine whether
a message is worth sending to the LLM for
memory extraction.

These patterns should stay lightweight.

The LLM decides WHAT memory to store.

The detector decides WHETHER to invoke the LLM.
"""

PATTERNS = [

    # ---------- Personal ----------
    r"\bmy name is\b",
    r"\bi am\b",
    r"\bi'm\b",
    r"\bmy birthday\b",
    r"\bi was born\b",
    r"\bi live in\b",
    r"\bi'm from\b",

    # ---------- Education ----------
    r"\bi study\b",
    r"\bi am studying\b",
    r"\bi graduated\b",
    r"\bi go to\b",
    r"\buniversity\b",
    r"\bcollege\b",

    # ---------- Work ----------
    r"\bi work\b",
    r"\bi am a\b",
    r"\bmy job\b",
    r"\bmy company\b",

    # ---------- Preferences ----------
    r"\bi like\b",
    r"\bi love\b",
    r"\bi prefer\b",
    r"\bi enjoy\b",
    r"\bi dislike\b",
    r"\bi hate\b",
    r"\bmy favorite\b",
    r"\bmy favourite\b",

    # ---------- Goals ----------
    r"\bi want to\b",
    r"\bi plan to\b",
    r"\bmy goal\b",
    r"\bi'm trying to\b",

    # ---------- Relationships ----------
    r"\bmy father\b",
    r"\bmy mother\b",
    r"\bmy brother\b",
    r"\bmy sister\b",
    r"\bmy friend\b",
    r"\bmy girlfriend\b",
    r"\bmy boyfriend\b",

    # ---------- Explicit ----------
    r"\bremember\b",
    r"\bdon't forget\b",
    r"\bkeep in mind\b",
]