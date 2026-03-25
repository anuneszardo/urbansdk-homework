from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Traffic Data API"
    DATABASE_URL: str = "postgresql://postgres:postgrespassword@db:5432/traffic_db"
    TEST_DATABASE_URL: str = "postgresql://postgres:postgrespassword@db:5432/traffic_test_db"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
