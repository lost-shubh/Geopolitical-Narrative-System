"""
Optional LLM client for counter-narrative synthesis.

The client intentionally uses plain HTTP so the project does not require an
OpenAI SDK dependency. It supports OpenAI's Responses API and the older
Chat Completions shape used by many OpenAI-compatible providers.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import requests

from src.utils.api_clients import load_api_config, load_pipeline_config


class LLMGenerationError(RuntimeError):
    """Raised when an LLM request cannot produce usable text."""


class LLMClient:
    """Small OpenAI/OpenAI-compatible text generation client."""

    def __init__(
        self,
        *,
        api_key: str = "",
        api_base: str = "https://api.openai.com/v1",
        provider: str = "openai_responses",
        model: str = "gpt-4.1-mini",
        timeout_seconds: int = 30,
        max_output_tokens: int = 700,
        temperature: float | None = 0.2,
        session: Any | None = None,
    ):
        self.api_key = api_key.strip()
        self.api_base = api_base.rstrip("/")
        self.provider = provider
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.session = session or requests
        self.last_error = ""

    @classmethod
    def from_config(
        cls,
        *,
        provider: str | None = None,
        model: str | None = None,
        api_base: str | None = None,
    ) -> "LLMClient":
        """Create a client from environment variables and YAML config."""
        pipeline_config = load_pipeline_config()
        api_config = load_api_config()

        api_key_env = api_config.get("llm_api_key_env", "OPENAI_API_KEY")
        api_base_env = api_config.get("llm_api_base_env", "GNS_LLM_API_BASE")

        return cls(
            api_key=os.getenv(api_key_env, api_config.get("llm_api_key", "")),
            api_base=api_base
            or os.getenv(api_base_env, api_config.get("llm_api_base", "https://api.openai.com/v1")),
            provider=provider or pipeline_config.get("llm_provider", "openai_responses"),
            model=model or os.getenv("GNS_LLM_MODEL", pipeline_config.get("llm_model", "gpt-4.1-mini")),
            timeout_seconds=int(pipeline_config.get("llm_timeout_seconds", 30)),
            max_output_tokens=int(pipeline_config.get("llm_max_output_tokens", 700)),
            temperature=pipeline_config.get("llm_temperature", 0.2),
        )

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.model)

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Generate text with the configured provider."""
        self.last_error = ""
        if not self.available:
            self.last_error = "LLM API key or model is not configured."
            raise LLMGenerationError(self.last_error)

        if self.provider in {"openai_responses", "responses"}:
            return self._generate_responses(system_prompt=system_prompt, user_prompt=user_prompt)
        if self.provider in {"openai_chat", "chat_completions", "chat"}:
            return self._generate_chat(system_prompt=system_prompt, user_prompt=user_prompt)

        self.last_error = f"Unsupported LLM provider: {self.provider}"
        raise LLMGenerationError(self.last_error)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _generate_responses(self, *, system_prompt: str, user_prompt: str) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "instructions": system_prompt,
            "input": user_prompt,
            "max_output_tokens": self.max_output_tokens,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature

        data = self._post_json(f"{self.api_base}/responses", payload)
        text = self._extract_responses_text(data)
        if not text:
            self.last_error = "LLM response did not contain output text."
            raise LLMGenerationError(self.last_error)
        return text

    def _generate_chat(self, *, system_prompt: str, user_prompt: str) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.max_output_tokens,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature

        data = self._post_json(f"{self.api_base}/chat/completions", payload)
        choices = data.get("choices", []) if isinstance(data, dict) else []
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, str) and content.strip():
                return content.strip()

        self.last_error = "Chat completion did not contain message content."
        raise LLMGenerationError(self.last_error)

    def _post_json(self, url: str, payload: Dict[str, Any]) -> Dict:
        try:
            response = self.session.post(
                url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code is None:
                status_code = getattr(locals().get("response", None), "status_code", None)
            detail = self._extract_error_detail(locals().get("response", None))
            if status_code:
                suffix = f" {detail}" if detail else ""
                self.last_error = f"LLM request failed with HTTP {status_code}.{suffix}"
            else:
                self.last_error = f"LLM request failed: {exc}"
            raise LLMGenerationError(self.last_error) from exc

    def _extract_error_detail(self, response: Any) -> str:
        """Extract a provider error message without exposing request secrets."""
        if response is None:
            return ""
        try:
            payload = response.json()
        except Exception:
            return ""
        if not isinstance(payload, dict):
            return ""
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message", "")
            code = error.get("code", "")
            error_type = error.get("type", "")
            parts = [str(part) for part in [error_type, code, message] if part]
            return " | ".join(parts)
        return ""

    def _extract_responses_text(self, data: Dict) -> str:
        if not isinstance(data, dict):
            return ""

        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        chunks: List[str] = []
        for item in data.get("output", []):
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if not isinstance(content, dict):
                    continue
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())

        return "\n".join(chunks).strip()
