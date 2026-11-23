import hashlib
from django.core.cache import cache

LOCATIONS_LIST_VERSION_KEY = "locations:list:version"
LOCATIONS_LIST_TTL = 60 * 5

def get_locations_cache_version():
    version = cache.get(LOCATIONS_LIST_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(LOCATIONS_LIST_VERSION_KEY, version, timeout=None)
    return int(version)


def bump_locations_cache_version() -> int:
    try:
        return cache.incr(LOCATIONS_LIST_VERSION_KEY)
    except ValueError:
        current = get_locations_cache_version() + 1
        cache.set(LOCATIONS_LIST_VERSION_KEY, current, timeout=None)
        return current


def build_locations_list_cache_key(request) -> str:
    version = get_locations_cache_version()
    items = sorted(request.query_params.lists())
    raw_query = "&".join(f"{k}={','.join(v)}" for k, v in items)
    digest = hashlib.md5(raw_query.encode("utf-8")).hexdigest()
    return f"locations:list:v{version}:{digest}"