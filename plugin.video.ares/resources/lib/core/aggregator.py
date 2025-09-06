from ..providers import a4k_adapter, coco_adapter
from ..utils.settings import get_str
from ..utils import cache
import json

def _cache_key(query, provider):
    q = dict(query); q.pop('action', None)
    return f"prov:{provider}:{json.dumps(q, sort_keys=True)}"

def aggregate_sources(query):
    enabled = [s.strip().lower() for s in get_str('enabled_providers','a4k,coco').split(',') if s.strip()]
    sources = []
    for prov, mod in (('a4k', a4k_adapter), ('coco', coco_adapter)):
        if prov not in enabled: continue
        key = _cache_key(query, prov)
        cached = cache.get(key)
        if cached:
            sources += cached; continue
        try:
            res = mod.search(query) or []
            cache.set(key, res, ttl=900)  # 15 min
            sources += res
        except Exception:
            pass
    # dedupe
    seen = set(); uniq = []
    for s in sources:
        key = s.get('magnet') or s.get('url') or s.get('title')
        if key in seen: continue
        seen.add(key); uniq.append(s)
    return uniq
