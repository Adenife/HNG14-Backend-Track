from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Profile Intelligence & Persistence API"
    PROJECT_VERSION: str = "1.0.1"

    GENDER_BASE_URL: str = "https://api.genderize.io/"
    AGIFY_BASE_URL: str = "https://api.agify.io/"
    NATIONALIZE_BASE_URL: str = "https://api.nationalize.io/"
    CLIENT_ORIGIN: str = "*"


settings = Settings()
