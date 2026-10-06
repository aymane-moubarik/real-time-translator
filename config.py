from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    mongo_uri: str
    mongo_db: str

    class Config:
        env_file = ".env"

settings = Settings()