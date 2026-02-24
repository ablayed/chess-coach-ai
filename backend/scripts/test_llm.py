"""Test that at least one LLM provider responds."""

from __future__ import annotations

import asyncio

from app.services.llm_service import LLMService


async def test() -> None:
    llm = LLMService()
    try:
        system = "You are a chess coach. Be concise."
        user = (
            "Position after 1.e4 e5 2.Nf3 Nc6 3.Bb5 (Ruy Lopez).\n"
            "The engine's best move for Black is 3...a6 (Morphy Defense).\n"
            "Explain why a6 is a good move in 3 sentences."
        )

        print("Calling LLM...")
        result = await llm.generate(system, user, max_tokens=300)
        print(f"\nLLM Response ({len(result)} chars):\n")
        print(result)
        print("\nLLM service is working!")
    except Exception as exc:  # noqa: BLE001
        print(f"LLM failed: {exc}")
        print("Check your API keys in .env")
    finally:
        await llm.close()


if __name__ == "__main__":
    asyncio.run(test())
