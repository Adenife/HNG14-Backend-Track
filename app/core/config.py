from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Natural Language Querying & Seeding"
    PROJECT_VERSION: str = "1.0.2"

    GENDER_BASE_URL: str = "https://api.genderize.io/"
    AGIFY_BASE_URL: str = "https://api.agify.io/"
    NATIONALIZE_BASE_URL: str = "https://api.nationalize.io/"
    CLIENT_ORIGIN: str = "*"

    DATABASE_PORT: int
    POSTGRES_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_HOSTNAME: str

    ENVIRONMENT: str

    class Config:
        env_file = "./.env"


settings = Settings()
