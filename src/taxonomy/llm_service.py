"""Small LLM wrapper used by the dynamic taxonomy scripts.

The production taxonomy runs use DeepSeek/OpenAI-compatible chat completion.
For dry-run sensitivity plumbing, set FYP_ALLOW_OFFLINE_TAXONOMY_LABELS=1 to
return deterministic placeholder labels without making an API call.
"""

from __future__ import annotations

import hashlib
import os
import re
from typing import Optional

from openai import OpenAI


class LLMService:
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or os.getenv("FYP_TAXONOMY_LLM_MODEL", "deepseek-chat")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.allow_offline = os.getenv("FYP_ALLOW_OFFLINE_TAXONOMY_LABELS", "0") == "1"

    @staticmethod
    def _offline_label(prompt: str) -> str:
        digest = hashlib.sha1(prompt.encode("utf-8", errors="ignore")).hexdigest()[:8]
        parent_match = re.search(r"broader '([^']+)' category", prompt)
        if "Decision:" in prompt or "TASK: Determine how to evolve" in prompt:
            return (
                "Decision: B\n"
                "Recommended_Name: Offline Existing Theme\n"
                "Parent_Macro: Offline Macro Theme\n"
                "Reasoning: Offline placeholder used for pipeline validation only."
            )
        if parent_match:
            return (
                f"Name: Offline Meso Theme {digest}\n"
                "Definition: Deterministic placeholder label for a meso risk cluster.\n"
                "Centroid_Summary: Placeholder semantic summary used only when offline labels are explicitly enabled."
            )
        return (
            f"Name: Offline Macro Theme {digest}\n"
            "Definition: Deterministic placeholder label for a macro risk cluster.\n"
            "Centroid_Summary: Placeholder semantic summary used only when offline labels are explicitly enabled."
        )

    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            if self.allow_offline:
                return self._offline_label(user_prompt)
            raise RuntimeError(
                "No DEEPSEEK_API_KEY or OPENAI_API_KEY is configured. "
                "Set FYP_ALLOW_OFFLINE_TAXONOMY_LABELS=1 for non-publication dry runs."
            )

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=float(os.getenv("FYP_TAXONOMY_LLM_TIMEOUT", "60")),
        )
        return response.choices[0].message.content or ""
