import os
import platform
import shutil

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # LLM API Keys
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    # Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 72

    # Stockfish
    STOCKFISH_PATH: str = "/usr/games/stockfish"
    STOCKFISH_DEPTH: int = 20
    STOCKFISH_HASH_MB: int = 128
    STOCKFISH_THREADS: int = 1
    STOCKFISH_POOL_SIZE: int = 2

    # App
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost,capacitor://localhost"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    def model_post_init(self, __context) -> None:  # type: ignore[override]
        if "STOCKFISH_PATH" in self.model_fields_set and self.STOCKFISH_PATH:
            return

        if self.STOCKFISH_PATH and os.path.exists(self.STOCKFISH_PATH):
            return

        discovered = shutil.which("stockfish")
        if discovered:
            self.STOCKFISH_PATH = discovered
            return

        if platform.system() == "Windows":
            candidates = [
                os.path.expanduser(r"~\stockfish\stockfish-windows-x86-64-avx2.exe"),
                os.path.expanduser(r"~\stockfish\stockfish.exe"),
                r"C:\stockfish\stockfish.exe",
                r"C:\stockfish\stockfish\stockfish-windows-x86-64-avx2.exe",
                "stockfish.exe",
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    self.STOCKFISH_PATH = candidate
                    return
            self.STOCKFISH_PATH = "stockfish.exe"
            return

        self.STOCKFISH_PATH = "/usr/games/stockfish"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
