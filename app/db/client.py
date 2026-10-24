from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache(maxsize=1)
def get_client() -> Client:
    settings.validate()
    return create_client(settings.supabase_url, settings.supabase_key)
