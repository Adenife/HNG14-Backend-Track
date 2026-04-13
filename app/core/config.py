from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Gender Classification System"
    PROJECT_VERSION: str = "1.0.0"

    GENDER_BASE_URL: str = "https://api.genderize.io/"
    CLIENT_ORIGIN: str = "*"


settings = Settings()
