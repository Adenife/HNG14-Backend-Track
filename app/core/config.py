from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Insighta Labs+"
    PROJECT_VERSION: str = "2.0.0"
    API_VERSION: str = "1"

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

    # GitHub OAuth
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 5

    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = "./.env"


settings = Settings()
