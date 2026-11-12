from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/transparenti.db"
    jwt_secret: SecretStr = SecretStr("troque-esta-chave-por-uma-com-no-minimo-32-bytes")
    jwt_issuer: str = "transparenti"
    jwt_audience: str = "transparenti-web"
    access_token_minutes: int = 480
    cors_origins: str = "http://localhost:3000"
    bootstrap_admin_email: str = "gestor@prefeitura.gov.br"
    bootstrap_admin_password: str = "troque-esta-senha"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
