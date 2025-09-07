import json, urllib.request, urllib.parse
from xbmcaddon import Addon
ADDON = Addon()
TMDB = "https://api.themoviedb.org/3"

def _get(path, params=None):
    key = ADDON.getSettingString('tmdb_api_key')
    params = params or {}
    if key: params["api_key"] = key
    url = TMDB + path + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode())

def find_show(title):
    try:
        s = _get("/search/tv", {"query": title})
        res = s.get("results") or []
        if not res: return None
        return res[0]
    except Exception:
        return None

def season_episode_count(tmdb_id, season_number):
    try:
        data = _get(f"/tv/{tmdb_id}/season/{season_number}")
        eps = data.get("episodes") or []
        return len(eps)
    except Exception:
        return 0

def compute_next(title, season, episode):
    # Resolve tmdb id and count to jump seasons properly
    show = find_show(title)
    if not show: 
        return season, episode + 1
    tmdb_id = show.get("id")
    count = season_episode_count(tmdb_id, season)
    if count and episode >= count:
        return season + 1, 1
    return season, episode + 1
