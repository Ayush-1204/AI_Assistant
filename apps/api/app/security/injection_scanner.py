import re

_INJECTION_PATTERNS = [
    (r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)", "prompt_override"),
    (r"(?i)you\s+are\s+now\s+(?:a\s+)?(?:different|new|my)", "identity_override"),
    (r"(?i)disregard\s+(?:all\s+)?(?:previous|prior|your)\s+(?:instructions?|programming|rules?)", "prompt_override"),
    (r"(?i)(?:execute|run|eval)\s*\(\s*['\"]", "code_injection"),
    (r"(?:;|\||&&)\s*(?:rm|curl|wget|nc|ncat|bash|sh|python|perl)\s", "shell_injection"),
    (r"(?i)(?:send|post|upload|exfiltrate|transmit)\s+(?:(?:to|data|all|everything)\s+)*(?:to\s+)?(?:https?://|my\s+server)", "exfiltration"),
    (r"(?i)(?:DAN|do\s+anything\s+now)\s+(?:mode|prompt|jailbreak)", "jailbreak"),
    (r"(?i)pretend\s+(?:you\s+)?(?:have\s+)?no\s+(?:restrictions?|limitations?|rules?|filters?)", "jailbreak"),
    (r"```(?:system|assistant)\b", "delimiter_injection"),
    (r"<\|(?:im_start|im_end|system|assistant)\|>", "delimiter_injection"),
]

class InjectionScanner:
    def __init__(self) -> None:
        self._patterns = [(re.compile(pat), name) for pat, name in _INJECTION_PATTERNS]

    def scan(self, text: str) -> dict:
        findings = []
        is_clean = True
        
        if not text:
            return {"is_clean": True, "findings": []}
            
        for pattern, name in self._patterns:
            if pattern.search(text):
                findings.append(name)
                is_clean = False
                
        return {
            "is_clean": is_clean,
            "findings": findings
        }
