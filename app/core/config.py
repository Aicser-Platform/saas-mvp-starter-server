from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/mvp_saas"
    SUPABASE_URL: str = ""           # e.g. https://xxxx.supabase.co
    SUPABASE_JWT_SECRET: str = ""    # only needed for HS256 projects (legacy)
    INTERNAL_API_SECRET: str = "stripe-webhook-internal-secret-2024"
    FRONTEND_URL: str = "http://localhost:3000"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
