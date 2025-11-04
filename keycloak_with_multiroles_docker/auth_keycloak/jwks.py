import requests
from asgiref.timeout import timeout
from django.core.cache import cache
from django.conf import settings

CACHE_KEY = "keycloak_jwks_cache"
CACHE_TTL = 60 * 15

def get_jwks(force: bool = False) -> dict:
    if not force:
        jwks = cache.get(CACHE_KEY)
        if jwks:
            return jwks

    response = requests.get(settings.KEYCLOAK_JWKS_URL, timeout=5)
    response.raise_for_status()
    jwks = response.json()
    cache.set(CACHE_KEY, jwks, CACHE_TTL)
    return jwks

# Preload JWKs during startup
def warm_jwks_cache() -> None:
  try:
    get_jwks(force=True)
  except Exception:
    pass