from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用运行时配置，优先从环境变量 / .env 读取。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "FlashApp Engine"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    host: str = "0.0.0.0"
    port: int = 8000

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "flashapp"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    qwen_base_url: str = "http://10.8.136.35:8081"
    seedcoder_base_url: str = "http://10.8.136.35:8881"
    embedding_base_url: str = "http://10.8.136.35:8002"
    reranker_base_url: str = "http://10.8.136.35:8003"
    deepseek_base_url: str = "http://10.32.129.214:8000"
    funasr_ws_url: str = "ws://10.17.150.235:10095"
    model_status_url: str = "http://10.17.150.235:30001/api/status"

    sandbox_port_min: int = 30000
    sandbox_port_max: int = 40000
    generated_code_root: str = "/tmp/flashapp/tasks"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
