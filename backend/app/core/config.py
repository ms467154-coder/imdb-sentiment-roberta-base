from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    model_path: str = "results/checkpoint-2480"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()
