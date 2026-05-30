import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "sua_chave_gemini"
    API_URL: str = "https://sua-api.com/endpoint"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    CHROMA_PERSIST_DIR: str = "storage/chroma"
    PDF_DIR: str = "data/pdfs"
    MOCK_API: bool = False
    MOCK_API_RESPONSE_PATH: str = "data/mock/api_response_example.json"
    REINDEX_ON_STARTUP: bool = False
    ADMIN_TOKEN: str = "troque_este_token"
    API_TIMEOUT_SECONDS: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
