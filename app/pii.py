from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    "cccd": r"\b\d{12}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "passport_vn": r"(?<![A-Z0-9])[A-Z]{1,2}\d{7}(?![A-Z0-9])",
    "address_vn": (
        r"(?i:\b(?:địa\s*chỉ|số\s+nhà|đường|phố|phường|xã|quận|huyện|"
        r"thị\s+(?:trấn|xã)|tỉnh|thành\s+phố)\b\s*[:\-]?\s*[^,;\n]{1,100})"
    ),
}

_COMBINED_PII_PATTERN = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in PII_PATTERNS.items())
)


def scrub_text(text: str) -> str:
    return _COMBINED_PII_PATTERN.sub(
        lambda match: f"[REDACTED_{match.lastgroup.upper()}]", text
    )


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
