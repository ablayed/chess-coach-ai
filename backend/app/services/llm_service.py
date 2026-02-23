import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Three-tier LLM fallback: Groq -> Gemini -> OpenRouter."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> str:
        providers = [
            ("groq", self._call_groq),
            ("gemini", self._call_gemini),
            ("openrouter", self._call_openrouter),
        ]

        last_error: Exception | None = None
        for name, call_fn in providers:
            try:
                result = await call_fn(system_prompt, user_prompt, max_tokens)
                logger.info("LLM response from %s (%s chars)", name, len(result))
                return result
            except Exception as exc:
                logger.warning("LLM provider %s failed: %s", name, exc)
                last_error = exc

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    async def _call_groq(self, system: str, user: str, max_tokens: int) -> str:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")

        resp = await self.client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, system: str, user: str, max_tokens: int) -> str:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set")

        resp = await self.client.post(
            (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            ),
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"parts": [{"text": user}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_openrouter(self, system: str, user: str, max_tokens: int) -> str:
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set")

        resp = await self.client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://chesscoach-ai.pages.dev",
            },
            json={
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def close(self) -> None:
        await self.client.aclose()
