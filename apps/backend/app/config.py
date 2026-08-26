from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "URAI Ransomware Resilience"
    environment: str = "development"
    demo_mode: bool = True


settings = Settings()