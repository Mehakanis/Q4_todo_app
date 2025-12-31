"""
Configuration settings for FastAPI backend.

This module loads environment variables and provides a Settings object
for the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.

    Attributes:
        database_url: PostgreSQL connection string (required)
        better_auth_url: Frontend URL for Better Auth JWKS endpoint
        frontend_url: Frontend URL for CORS
        debug: Enable debug mode (default: False)
        environment: Environment name (default: "development")
        kafka_brokers: Kafka broker addresses (Phase V)
        dapr_http_port: Dapr sidecar HTTP port (Phase V)
        dapr_grpc_port: Dapr sidecar gRPC port (Phase V)
        smtp_host: SMTP server hostname (Phase V)
        smtp_port: SMTP server port (Phase V)
        smtp_user: SMTP username (Phase V)
        smtp_password: SMTP password (Phase V)
    """

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "")
        # Better Auth URL - frontend URL where Better Auth is hosted
        # Priority: BETTER_AUTH_URL > NEXT_PUBLIC_APP_URL > default
        self.better_auth_url = (
            os.getenv("BETTER_AUTH_URL") or
            os.getenv("NEXT_PUBLIC_APP_URL") or
            "https://todo-giaic-five-phases.vercel.app"  # Production default
        )
        self.frontend_url = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")[0]
        self.debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        self.environment = os.getenv("ENVIRONMENT", "development")

        # Phase V: Kafka configuration
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka:9092")

        # Phase V: Dapr configuration
        self.dapr_http_port = int(os.getenv("DAPR_HTTP_PORT", "3500"))
        self.dapr_grpc_port = int(os.getenv("DAPR_GRPC_PORT", "50001"))
        self.dapr_url = f"http://localhost:{self.dapr_http_port}"

        # Phase V: SMTP configuration for notification service
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")

        # Log configuration for debugging
        if self.environment != "production":
            print(f"[CONFIG] Better Auth URL: {self.better_auth_url}")
            print(f"[CONFIG] Frontend URL: {self.frontend_url}")
            print(f"[CONFIG] Kafka Brokers: {self.kafka_brokers}")
            print(f"[CONFIG] Dapr HTTP Port: {self.dapr_http_port}")


settings = Settings()

