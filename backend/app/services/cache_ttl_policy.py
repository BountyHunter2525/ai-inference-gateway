"""
Adaptive TTL Policy
====================
Classifies a prompt into one of three stability tiers and returns the
appropriate Time-To-Live in seconds.

Tier       TTL (default)   Rationale
---------  --------------  ---------------------------------------------------
factual    24 h (86 400 s) Stable facts: definitions, capitals, history, math
technical  6 h  (21 600 s) Code/how-to/architecture: changes infrequently
general    1 h  ( 3 600 s) Everything else — safe conservative window

The classifier uses keyword matching (no ML needed) so it runs in O(n)
time at negligible cost before every cache-store operation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import settings

# ── Keyword patterns per tier ─────────────────────────────────────────────────

_FACTUAL_PATTERNS: list[re.Pattern[str]] = [re.compile(p, re.IGNORECASE) for p in [
    r"\bwhat\s+is\s+the\s+capital\b",
    r"\bwho\s+(is|was|invented|discovered|founded)\b",
    r"\bwhen\s+(was|did|is)\b",
    r"\bwhere\s+is\b",
    r"\bdefinition\s+of\b",
    r"\bdefine\b",
    r"\bmeaning\s+of\b",
    r"\bhistory\s+of\b",
    r"\bbiography\b",
    r"\bformula\s+for\b",
    r"\bmath(ematics)?\b",
    r"\bequation\b",
    r"\btheorem\b",
    r"\bscientific\s+(law|fact|principle)\b",
    r"\bcountry\b",
    r"\bcapital\s+(city|of)\b",
    r"\bflag\s+of\b",
    r"\bpopulation\s+of\b",
    r"\bfound(er|ed)?\b",
    r"\bgeograph(y|ic)\b",
]]

_TECHNICAL_PATTERNS: list[re.Pattern[str]] = [re.compile(p, re.IGNORECASE) for p in [
    r"\bhow\s+(do|does|to)\b",
    r"\bexplain\b",
    r"\barchitecture\b",
    r"\bmicroservice\b",
    r"\bkubernetes\b",
    r"\bdocker\b",
    r"\bapi\b",
    r"\brest(ful)?\b",
    r"\bgraph(ql)?\b",
    r"\bdatabase\b",
    r"\bsql\b",
    r"\bnosql\b",
    r"\balgorithm\b",
    r"\bdata\s+structure\b",
    r"\bdesign\s+pattern\b",
    r"\bcode\b",
    r"\bprogram(ming)?\b",
    r"\bfunction\b",
    r"\bclass\b",
    r"\bobject[-\s]oriented\b",
    r"\bdeployment\b",
    r"\bci/cd\b",
    r"\bgit\b",
    r"\bversion\s+control\b",
    r"\bmachine\s+learning\b",
    r"\bneural\s+network\b",
    r"\bdeep\s+learning\b",
    r"\bpython\b",
    r"\bjava(script)?\b",
    r"\btypescript\b",
    r"\brust\b",
    r"\bgo(lang)?\b",
    r"\bcloud\b",
    r"\baws\b",
    r"\bazure\b",
    r"\bgcp\b",
    r"\binfrastructure\b",
    r"\bnetwork(ing)?\b",
    r"\bprotocol\b",
    r"\bhttp(s)?\b",
    r"\btcp\b",
    r"\bdns\b",
    r"\bssl\b",
    r"\btls\b",
]]


@dataclass(frozen=True)
class TTLDecision:
    ttl_seconds: int
    category: str   # "factual" | "technical" | "general"
    matched_pattern: str | None = None


class CacheTTLPolicy:
    """
    Stateless classifier — instantiate once as a module-level singleton.

    Usage::

        from app.services.cache_ttl_policy import ttl_policy
        decision = ttl_policy.decide(prompt)
        semantic_cache.store(..., ttl_seconds=decision.ttl_seconds)
    """

    def decide(self, prompt: str) -> TTLDecision:
        """
        Classify *prompt* and return a TTLDecision.

        Factual patterns are checked first (highest confidence, longest TTL),
        then technical. Anything else falls through to general.
        """
        cleaned = prompt.strip()

        for pattern in _FACTUAL_PATTERNS:
            m = pattern.search(cleaned)
            if m:
                return TTLDecision(
                    ttl_seconds=settings.CACHE_TTL_FACTUAL,
                    category="factual",
                    matched_pattern=m.group(0),
                )

        for pattern in _TECHNICAL_PATTERNS:
            m = pattern.search(cleaned)
            if m:
                return TTLDecision(
                    ttl_seconds=settings.CACHE_TTL_TECHNICAL,
                    category="technical",
                    matched_pattern=m.group(0),
                )

        return TTLDecision(
            ttl_seconds=settings.CACHE_TTL_GENERAL,
            category="general",
        )

    def category_label(self, prompt: str) -> str:
        """Convenience wrapper returning just the category string."""
        return self.decide(prompt).category


ttl_policy = CacheTTLPolicy()
