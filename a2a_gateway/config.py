"""Configuration management for A2A Coding Gateway"""

from pydantic_settings import BaseSettings
from pydantic.fields import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Gateway configuration
    host: str = Field(default="0.0.0.0", description="Gateway host address")
    port: int = Field(default=8000, description="Gateway port")
    max_concurrent_tasks: int = Field(
        default=5, description="Maximum number of concurrent tasks"
    )
    default_timeout: int = Field(
        default=600, description="Default task timeout in seconds"
    )
    task_timeout: int = Field(
        default=300, description="Task execution timeout in seconds"
    )

    # Redis configuration
    redis_url: Optional[str] = Field(
        default=None, description="Redis connection URL (optional)"
    )
    redis_enabled: bool = Field(
        default=False, description="Whether to use Redis for task storage"
    )
    task_retention_days: int = Field(
        default=7, description="Number of days to retain completed tasks"
    )

    # Tools configuration
    droid_command: str = Field(default="droid", description="Command to run droid")
    claude_command: str = Field(
        default="claude", description="Command to run Claude Code"
    )

    # Security configuration
    api_key: Optional[str] = Field(
        default=None, description="API Key for authentication (optional)"
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "https://yourdomain.com"],
        description="Allowed CORS origins",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG/INFO/WARNING/ERROR)"
    )
    log_format: str = Field(default="json", description="Logging format (json/console)")
    log_file: str = Field(
        default="/var/log/a2a-gateway/gateway.log", description="Log file path"
    )

    # Monitoring configuration
    metrics_enabled: bool = Field(
        default=True, description="Whether to enable Prometheus metrics"
    )
    metrics_port: int = Field(default=8000, description="Port to expose metrics on")

    class Config:
        """Settings configuration"""

        env_prefix = "A2A_"
        case_sensitive = False
        env_file = ".env"


settings = Settings()
