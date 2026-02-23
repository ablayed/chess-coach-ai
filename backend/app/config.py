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
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
